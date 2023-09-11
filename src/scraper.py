import csv
import getpass
import os
import re
import sys
from enum import Enum
import argparse

import pandas as pd
import pdfplumber
import requests
from bs4 import BeautifulSoup
from colorama import Fore, Style, Back, ansi
import click
from colorama import init as colorama_init
from selenium import webdriver
from selenium.webdriver.common.by import By as BY
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait


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

greek_alphabet = "ΑαΒβΓγΔδΕεΖζΗηΘθΙιΚκΛλΜμΝνΞξΟοΠπΡρΣσςΤτΥυΦφΧχΨψΩω"
latin_alphabet = "AaBbGgDdEeZzHhJjIiKkLlMmNnXxOoPpRrSssTtYyFfQqYyWw"
greek2latin = str.maketrans(greek_alphabet, latin_alphabet)


def clr(colorama_style: list[ansi.AnsiFore | ansi.AnsiStyle], string: str):
    return f"{''.join(colorama_style)}{string}{Style.RESET_ALL}"

def init():
    colorama_init()
    # check cache dir
    if not os.path.exists(CACHE_PATH):
        os.makedirs(CACHE_PATH)

def main():
    init()
    parser = argparse.ArgumentParser(description="Command-line tool for managing courses and degree completion.")

    parser.add_argument('--courses', action='store_true', help='Show available courses this semester')
    parser.add_argument('--degree', action='store_true', help="Show stats on on your degree's completion")

    args = parser.parse_args()
    parser.set_defaults(func=parser.print_help)

    if len(sys.argv) == 1:
        parser.print_help()
        return

    if args.courses:
        courses_to_take()

    if args.degree:
        check_degre_completion()


def courses_to_take():
    schedule = get_semester_schedule()
    courses = get_courses()
    grades = get_grades()

    completed_courses = pd.merge(
        courses.drop(columns=["NAME"]), grades, on=["ECTS", "ID"], how="right"
    )
    completed_courses["TYPE"] = completed_courses["TYPE"].fillna(CourseType.FREE.name)

    non_completed = schedule[~schedule["ID"].isin(completed_courses["ID"])]
    desired_types = ["E3", "E4", "E5", "E6", "E7", "E8", "E9"]
    type_counts = completed_courses["TYPE"][
        completed_courses["TYPE"].isin(desired_types)
    ].value_counts()
    excided_number_of_type = type_counts[type_counts >= 3].index.tolist()
    available_courses = pd.merge(
        courses.drop(columns=["RECOMMENDED","NAME"]), non_completed, on=["ID"], how="inner"
    )
    available_courses = available_courses[
        ~available_courses["TYPE"].isin(excided_number_of_type)
    ]
    print(available_courses)


def check_degre_completion():
    def check(contition: bool):
        return (
            clr([Style.BRIGHT, Fore.GREEN], "PASS")
            if contition
            else clr([Style.BRIGHT, Fore.RED], "FAIL")
        )

    def head_sep():
        print(clr(Style.BRIGHT, "=" * 68))

    def sep():
        print(clr(Style.BRIGHT, "-" * 40))

    def pad(depth: int):
        return " " * 4 * depth

    def print_table(depth: int, courses: pd.DataFrame, cols: list):
        text_courses = ["NONE"]
        if not courses.empty:
            text_courses = (
                courses[cols].to_string(index=False, justify="left").splitlines()
            )
        print(clr(Style.BRIGHT, text_courses[0]))
        for course in text_courses[1:]:
            print(pad(depth) + course)
        print()

    important_cols = ["ECTS", "ID", "NAME"]
    courses = get_courses()
    grades = get_grades()

    completed_courses = pd.merge(
        courses.drop(columns=["NAME"]), grades, on=["ECTS", "ID"], how="right"
    )
    completed_courses["TYPE"] = completed_courses["TYPE"].fillna(CourseType.FREE.name)

    head_sep()
    print()

    print(f"{clr(Style.BRIGHT,'[1]')} At least 8 semesters :")
    sep()
    print("LOL")
    print()

    print(f"{clr(Style.BRIGHT,'[2]')} All BASE courses :")
    sep()
    base_courses = courses[courses["TYPE"] == "BASE"]
    completed_base_courses = completed_courses[completed_courses["TYPE"] == "BASE"]
    missing_base_courses = base_courses[
        ~base_courses["ID"].isin(completed_base_courses["ID"])
    ]
    missing_base_courses_text = (
        missing_base_courses[important_cols].to_string(index=False).splitlines()
    )
    for base in missing_base_courses_text:
        print(pad(1) + base)
    print()

    print(f"{clr(Style.BRIGHT,'[3]')} 20 ECTS from E1>=2 or E2<=1 :")
    sep()
    completed_E1E2_courses = completed_courses[
        (completed_courses["TYPE"] == "E1") | (completed_courses["TYPE"] == "E2")
    ]

    # print(completed_E1E2_courses)
    E1 = completed_E1E2_courses[completed_E1E2_courses["TYPE"] == "E1"]
    E2 = completed_E1E2_courses[completed_E1E2_courses["TYPE"] == "E2"]
    E1_ects = 0 if E1.empty else E1["ECTS"].sum()
    E2_ects = 0 if E2.empty else E2["ECTS"].max()

    E1E2_ects = E1_ects + E2_ects

    print("You need at least 2 E1 courses passed.")
    print(f"{pad(1)}{ clr( Style.BRIGHT, 'E1') }: {len(E1)} passed courses ({E1_ects})")
    print()
    print_table(2, E1, important_cols)
    print()
    print("You need at most 1 E2 courses passed.(If more than 1 the max is taken)")
    print(f"{pad(1)}{ clr( Style.BRIGHT, 'E2') }: {len(E2)} passed courses ({E2_ects})")
    print()
    print_table(2, E2, important_cols)

    print(
        f"You have {clr( Style.BRIGHT,E1E2_ects )} out of 20: { check(E1E2_ects>=20) }"
    )
    print()

    print(f"{clr(Style.BRIGHT,'[4]')} E3-E9 Courses :")
    sep()
    # completed_courses[]

    desired_types = ["E3", "E4", "E5", "E6", "E7", "E8", "E9"]
    completed_E3toE9_courses = completed_courses[
        completed_courses["TYPE"].isin(desired_types)
    ]

    def sum_of_3_largest(group):
        return group.nlargest(3, "ECTS")["ECTS"].sum()

    # Group by 'TYPE' and apply the sum_of_3_largest function
    result = (
        completed_E3toE9_courses.groupby("TYPE")
        .apply(sum_of_3_largest)
        .reset_index(name="Sum_of_3_Largest")
    )
    print_table(1, result, ["TYPE", "Sum_of_3_Largest"])
    print()

    print(f"{clr(Style.BRIGHT,'[5]')} One FREE course or n>3 E3-E9 Courses :")
    sep()
    print_table(
        1,
        completed_courses[completed_courses["TYPE"] == "FREE"][important_cols],
        important_cols,
    )

    print(f"{clr(Style.BRIGHT,'[6]')} 240 ECTS :")
    sep()
    all_ects = completed_courses["ECTS"].sum()
    print(
        f"{pad(1)}{clr( Style.BRIGHT,'ECTS' )}: {all_ects} out of 240  {check(all_ects>=240)}"
    )


def get_grades(ignore_cache: bool = False) -> pd.DataFrame:
    if not os.path.exists(GRADES_CACHE) or ignore_cache:
        print("Please wait while we fetch your grades...")
        fetch_grades()
    df = pd.read_csv(GRADES_CACHE, delimiter="|")
    return df


def get_semester_schedule(ignore_cache: bool = False) -> pd.DataFrame:
    if not os.path.exists(SCEDULE_CACHE) or ignore_cache:
        fetch_schedule()

    columns = [
        "ID",
        "NAME",
        "TEACHER",
        "MONDAY",
        "TUESDAY",
        "WEDNESDAY",
        "THURSDAY",
        "FRIDAY",
    ]
    df = pd.read_csv(SCEDULE_CACHE, delimiter="|", index_col=False, names=columns)

    return df


def fetch_schedule():
    with open(SCEDULE_CACHE, "w",encoding="utf-8") as schedule_cache:
        csv_writer = csv.writer(schedule_cache, delimiter="|")

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
        for row in data:
            row[0] = row[0].translate(greek2latin)
        csv_writer.writerows(data)


def download_file(url, path) -> None:
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
    df["ECTS"] = pd.to_numeric(df["ECTS"], errors="coerce")
    return df


def fetch_grades() -> None:
    options = webdriver.FirefoxOptions()
    options.add_argument("-headless")
    driver = webdriver.Firefox(options=options)
    # driver = webdriver.Firefox()

    email, password = get_credentials()

    driver.get(
        "https://sso.uoc.gr/login?service=https%3A%2F%2Feduportal.cict.uoc.gr%2Flogin%2Fcas"
    )
    driver.find_element("id", "username").send_keys(email)
    driver.find_element("id", "password").send_keys(password)
    driver.find_element("name", "submit").click()
    # wait the ready state to be complete
    wait = WebDriverWait(driver=driver, timeout=10)
    wait.until(lambda x: x.execute_script("return document.readyState === 'complete'"))
    error_message = "Invalid credentials."

    errors = driver.find_elements(BY.CSS_SELECTOR, "#fm1 > div > span")

    for e in errors:
        print(e.text)

    if any(error_message in e.text for e in errors):
        print("[!] Login failed")
        exit(1)
    else:
        print("[+] Login successful")

    grades = (
        BY.CSS_SELECTOR,
        ".side-menu > div:nth-child(1) > li:nth-child(5) > ul:nth-child(2) > li:nth-child(1) > a:nth-child(1)",
    )

    grades_element = wait.until(EC.presence_of_element_located(grades))

    driver.get(grades_element.get_attribute("href"))

    select = (BY.CSS_SELECTOR, "#options")
    table = (BY.CSS_SELECTOR, "#student_grades_diploma")
    driver.implicitly_wait(0.5)
    select_element = wait.until(EC.element_to_be_clickable(select))
    dropdown = Select(select_element)

    wait.until(
        EC.invisibility_of_element_located(
            (BY.CSS_SELECTOR, "div.blockUI.blockOverlay")
        )
    )
    driver.implicitly_wait(0.5)
    dropdown.select_by_index(2)
    driver.implicitly_wait(0.5)

    page_source = driver.page_source
    driver.quit()

    with open(GRADES_CACHE, "w",encoding="utf-8") as grades_cache:
        csv_writer = csv.writer(grades_cache, delimiter="|")
        soup = BeautifulSoup(page_source, "html.parser")
        table = soup.find("table", id="student_grades_diploma")
        headers = [
            "ID",
            "NAME",
            "GRADE",
            "EXAM_PERIOD",
            "YEAR",
            "RD",
            "RG",
            "CP",
            "ECTS",
            "OPTIONAL",
            "CATEGORY",
        ]
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
                    checkbox = column.find("input", type="checkbox")
                    if checkbox:
                        data.append("checked" in checkbox.attrs)
                        continue
                    else:
                        data.append(column.get_text(strip=True))
                grades.append(data[:-2])
        for row in grades:
            row[0] = row[0].translate(greek2latin)
        csv_writer.writerows(grades)


def fetch_courses() -> None:
    with open(COURSE_CACHE, "w",encoding="utf-8") as courses:
        csv_writer = csv.writer(courses, delimiter="|")
        headings = ["TYPE", "ID", "NAME", "ECTS", "DEPENDENCIES", "RECOMMENDED"]
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
                    data[0] = data[0].translate(greek2latin)
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


if __name__ == "__main__":
    main()
