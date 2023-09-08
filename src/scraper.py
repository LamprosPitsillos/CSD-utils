import requests
import csv
import re
from bs4 import BeautifulSoup
import pandas as pd
from enum import Enum
from unidecode import unidecode
import os
import getpass
import pdfplumber

# from selenium import webdriver
# from selenium.webdriver.common.keys import Keys

class CourseType(Enum):
    BASE="ΚΟΡΜΟΥ"
    E1="E1"
    E2="E2"
    E3="E3"
    E4="E4"
    E5="E5"
    E6="E6"
    E7="E7"
    E8="E8"
    E9="E9"
    FREE="ΕΛΕΦΘΕΡΗΣ"

COURSE_CACHE_PATH = "cources.csv"

UNI_URL="https://www.csd.uoc.gr/CSD"
UNI_CONTENT_URL=f"{UNI_URL}/index.jsp?content"
UNI_UPLOADS_URL=f"{UNI_URL}uploaded_files"
# UNI_UPLOADS_URL="https://www.csd.uoc.gr/CSD/uploaded_files/WROLOGIO%20PROGRAMMA%20XEIMERINOY%20E3AMHNOY%202023-24_ekdosh5-9-2023.pdf"
def main():
    # get_courses()
    print(get_semester_schedule())
    pass

def get_semester_schedule():

    directory="."
    page = get_content_page("akadimaiko_hmerologio")
    soup = BeautifulSoup(page.content, "html.parser")
    pattern =re.compile("Ωρολόγιο πρόγραμμα")
    url = soup.find("a",string=pattern).get("href")

    path = os.path.join(directory, os.path.basename(url))
    if not os.path.exists(path) : 
        download_file(url,path)

    data = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if table:
                table = table[1:]
                data.extend(table)

    # Convert the extracted data into a pandas DataFrame
    df = pd.DataFrame(data)

    return df

def download_file(url, path):
    response = requests.get(url)
    if response.status_code == 200:
        with open(path, 'wb') as file:
            file.write(response.content)
        print(f"Downloaded: {path}")
    else:
        print(f"Failed to download: {url}")

def get_courses(ignore_cache:bool = False)-> pd.DataFrame:
    if not os.path.exists(COURSE_CACHE_PATH) or ignore_cache:
        fetch_courses()

    df = pd.read_csv(COURSE_CACHE_PATH,delimiter='|',index_col=False,header=0)
    print(df)

def fetch_courses() -> None:
        with open(COURSE_CACHE_PATH, 'w') as courses:
            csv_writer = csv.writer(courses,delimiter='|')
            headings = ["TYPE","ID","NAME","ECTS","DEPENDENCIES"]
            csv_writer.writerow(headings)

            page=get_content_page("courses_catalog")
            soup = BeautifulSoup(page.content, "html.parser")
            results = soup.find_all("table")
            for table in results:
                table_header=table.find("th")
                if table_header:
                    courses_desc: str = table_header.get_text(strip=True)
                    courses_type: CourseType = get_courses_type(courses_desc)
                    rows=table.find_all("tr")
                    for row in rows:
                        columns:list = row.find_all("td")
                        if not columns : continue
                        data = [column.get_text(strip=True) for column in columns]
                        data.insert(0,courses_type.name)
                        csv_writer.writerow(data)

def get_courses_type(courses_desc:str)->CourseType:
            pattern = re.compile(r'\((.*?)\)')
            courses_type = pattern.search(courses_desc)

            if courses_type :
                # Some are greek some are english smh....
                type_found=unidecode( courses_type.group(1))
                return CourseType(type_found)
            else:
                if courses_desc == "Μαθήματα Ελεύθερης Επιλογής":
                    return CourseType.FREE
                elif courses_desc == "Μαθήματα κορμού": 
                    return CourseType.BASE

            assert "No valid course type found"


def get_content_page(content:str)-> requests.Response:
    return requests.get(f"{UNI_CONTENT_URL}={content}")

def get_uploaded_files(file_name:str)-> requests.Response:
    assert false

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

