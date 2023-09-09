import csv
import getpass
import os
import re
from enum import Enum

import pandas as pd
import pdfplumber
import requests
from bs4 import BeautifulSoup
from unidecode import unidecode

# from selenium import webdriver
# from selenium.webdriver.common.keys import Keys

greek_alphabet = 'ΑαΒβΓγΔδΕεΖζΗηΘθΙιΚκΛλΜμΝνΞξΟοΠπΡρΣσςΤτΥυΦφΧχΨψΩω'
latin_alphabet = 'AaBbGgDdEeZzHhJjIiKkLlMmNnXxOoPpRrSssTtYyFfQqYyWw'
greek2latin = str.maketrans(greek_alphabet, latin_alphabet)

class CourseType(Enum):
    BASE = "ΚΟΡΜΟΥ"
    E1 = "E1"
    E2 = "E2"
    E3 = "E3"
    E4 = "E4"
    E5 = "E5"
    E6 = "E6"
    E7 = "E7"
    E8 = "E8"
    E9 = "E9"
    FREE = "ΕΛΕΦΘΕΡΗΣ"


CACHE_PATH = "cache"
COURSE_CACHE = f"{CACHE_PATH}/cources.csv"
GRADES_CACHE = f"{CACHE_PATH}/grades.csv"
SCEDULE_CACHE = f"{CACHE_PATH}/schedule.csv"

UNI_URL = "https://www.csd.uoc.gr/CSD"
UNI_CONTENT_URL = f"{UNI_URL}/index.jsp?content"
UNI_UPLOADS_URL = f"{UNI_URL}uploaded_files"
# UNI_UPLOADS_URL="https://www.csd.uoc.gr/CSD/uploaded_files/WROLOGIO%20PROGRAMMA%20XEIMERINOY%20E3AMHNOY%202023-24_ekdosh5-9-2023.pdf"


def main():
    check_degre_completion()
    pass

def check_degre_completion():
    courses = get_courses()
    semester_schedule = get_semester_schedule()
    grades = get_grades()

    # print(grades.columns.values)
    # print(courses.columns.values)

    completed_courses=pd.merge(courses, grades, on=[ 'ID' ],how="inner")

    #1 8 Semesters LOL

    #2 All BASE courses

    print(pd.merge(completed_courses,courses,on="ID",how="inner"))
    # print(grades)
    # print(courses)






def get_grades(ignore_cache:bool =False)->pd.DataFrame:
    if not os.path.exists(GRADES_CACHE) or ignore_cache:
        fetch_grades()
    df = pd.read_csv(GRADES_CACHE,delimiter='|')
    return df


def get_semester_schedule(ignore_cache:bool =False)->pd.DataFrame:
    if not os.path.exists(SCEDULE_CACHE) or ignore_cache:
        fetch_schedule()

    df = pd.read_csv(SCEDULE_CACHE, delimiter="|", index_col=False)
    return df


def fetch_schedule():
    with open( SCEDULE_CACHE, "w") as schedule_cache:
        csv_writer = csv.writer(schedule_cache,delimiter='|')

        page = get_content_page("akadimaiko_hmerologio")
        soup = BeautifulSoup(page.content, "html.parser")
        pattern = re.compile("Ωρολόγιο πρόγραμμα")
        url = soup.find("a", string=pattern).get("href")

        path = os.path.join(CACHE_PATH, os.path.basename(url))
        if not os.path.exists(path):
            download_file(url, path)

        data = []
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                table = page.extract_table()
                if table:
                    table = table[1:]
                    data.extend(table)
        csv_writer.writerows(data)



def download_file(url, path)->None:
    response = requests.get(url)
    if response.status_code == 200:
        with open(path, "wb") as file:
            file.write(response.content)
        print(f"Downloaded: {path}")
    else:
        print(f"Failed to download: {url}")


def get_courses(ignore_cache: bool = False) -> pd.DataFrame:
    if not os.path.exists(COURSE_CACHE) or ignore_cache:
        fetch_courses()

    df = pd.read_csv(COURSE_CACHE, delimiter="|", index_col=False)

    return df


def fetch_grades()->None:
    print("Fetching Grades from File")
    if not os.path.exists("grades.html"):
        print(
            "Please download the HTML from eduportal. Login , right click, download HTML"
        )
        exit(1)

    with open("grades.html", "r") as grades_file, open( GRADES_CACHE, "w") as grades_cache:
        csv_writer = csv.writer(grades_cache, delimiter="|")
        soup = BeautifulSoup(grades_file, "html.parser")
        table = soup.find("table", id="student_grades_diploma")
        headers = ["ID","COURSE","GRADE","EXAM_PERIOD","YEAR","RD","RG","CP","ECTS","OPTIONAL","CATEGORY"]
        csv_writer.writerow(headers)
        table_body = table.find("tbody")
        grades = []
        if table_body:
            rows = table.select("tr:not(.group)")
            for row in rows:
                columns: list = row.find_all("td")
                if not columns:
                    continue
                data = []
                for column in columns:
                    checkbox=column.find("input",type="checkbox")
                    if checkbox :
                        data.append("checked" in checkbox.attrs)
                        continue
                    else :
                        data.append(column.get_text(strip=True))
                grades.append(data[:-2])
        for row in grades:
           row[0]=row[0].translate(greek2latin)
        csv_writer.writerows(grades)


def fetch_courses() -> None:
    with open(COURSE_CACHE, "w") as courses:
        csv_writer = csv.writer(courses, delimiter="|")
        headings = ["TYPE", "ID", "NAME", "ECTS", "DEPENDENCIES"]
        csv_writer.writerow(headings)

        page = get_content_page("courses_catalog")
        soup = BeautifulSoup(page.content, "html.parser")
        results = soup.find_all("table")
        for table in results:
            table_header = table.find("th")
            if table_header:
                courses_desc: str = table_header.get_text(strip=True)
                courses_type: CourseType = get_courses_type(courses_desc)
                rows = table.find_all("tr")
                for row in rows:
                    columns: list = row.find_all("td")
                    if not columns:
                        continue
                    data = [column.get_text(strip=True) for column in columns]
                    data[0]=data[0].translate(greek2latin)
                    data.insert(0, courses_type.name)
                    csv_writer.writerow(data)

def get_courses_type(courses_desc: str) -> CourseType:
    pattern = re.compile(r"\((.*?)\)")
    courses_type = pattern.search(courses_desc)

    if courses_type:
        # Some are greek some are english smh....
        type_found = (courses_type.group(1)).translate(greek2latin)
        return CourseType(type_found)
    else:
        if courses_desc == "Μαθήματα Ελεύθερης Επιλογής":
            return CourseType.FREE
        elif courses_desc == "Μαθήματα κορμού":
            return CourseType.BASE

    assert "No valid course type found"


def get_content_page(content: str) -> requests.Response:
    return requests.get(f"{UNI_CONTENT_URL}={content}")

# ====================================================
#


def get_credentials():
    print("Please enter your credentials:")
    username = input("Email: ")
    password = getpass.getpass("Password (hidden): ")
    return username, password


def get_courses_completions():
    pass


#
# # Set the path to your WebDriver executable (e.g., chromedriver)
#     webdriver_path = '/path/to/chromedriver'
#
# # Initialize the web driver (replace 'chrome' with 'firefox' if using Firefox)
#     driver = webdriver.Chrome(executable_path=webdriver_path)
#
# # Navigate to the login page
#     driver.get('https://example.com/login')
#
# # Find and fill in the username and password fields
#     username_field = driver.find_element_by_name('username')  # Replace with the actual field name
#     password_field = driver.find_element_by_name('password')  # Replace with the actual field name
#     username_field.send_keys('your_username')
#     password_field.send_keys('your_password')
#
# # Submit the login form
#     password_field.send_keys(Keys.RETURN)
#
# # Wait for a few seconds (adjust as needed) to ensure the login process completes
#     time.sleep(5)
#
# # Now that you're logged in, navigate to the dashboard or the page you want to scrape
#     driver.get('https://example.com/dashboard')
#
# # Extract data from the dashboard page using Selenium selectors
#     data_field_1 = driver.find_element_by_css_selector('selector_for_data_1').text
#     data_field_2 = driver.find_element_by_css_selector('selector_for_data_2').text
# # Add more fields as needed
#
# # Print or process the retrieved data
#     print('Data Field 1:', data_field_1)
#     print('Data Field 2:', data_field_2)
#
# # Close the browser when done
#     driver.quit()

if __name__ == "__main__":
    main()
