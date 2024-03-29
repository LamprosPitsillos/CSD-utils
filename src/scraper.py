import csv
import os
import re
from enum import Enum

import click
import pandas as pd
import pdfplumber
import pwinput
import requests
from bs4 import BeautifulSoup

# from click import cli ,click
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException ,TimeoutException
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
    FREE = "ΕΛΕΥΘΕΡΗΣ"


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

SUPPORTED_OUTPUTS = ["csv", "pdf", "md"]


def init():
    # check cache dir
    if not os.path.exists(CACHE_PATH):
        os.makedirs(CACHE_PATH)


@click.group()
def cli():
    """A simple utility for CSD students."""
    pass


@cli.command()
# @click.option(
#     "--format", type=click.Choice(["csv", "pdf", "md"]), default="md", required=False
# )
# @click.option(
#     "--output", type=click.Path(), default="stdout", help="Output filename (optional)"
# )
def degree():
    """Command to handle degree-related tasks."""
    check_degree_completion()


@cli.command()
@click.option(
    "--format",
    type=click.Choice(["csv", "pdf", "md", "json", "pretty"]),
    default="pretty",
    required=False,
)
# @click.option(
#     "--output", type=click.Path(), default="stdout", help="Output filename (optional)"
# )
def courses(format):
    """Command to handle courses-related tasks."""
    courses_to_take(format)


@cli.command()
def clearcache():
    """Command to clear cache."""
    # Implement cache clearing logic here
    # Check if the directory exists
    if os.path.exists(CACHE_PATH) and os.path.isdir(CACHE_PATH):
        # List all files in the directory
        files = os.listdir(CACHE_PATH)

        # Iterate over each file in the directory
        for file_name in files:
            # Construct the full file path
            file_path = os.path.join(CACHE_PATH, file_name)

            # Check if it's a file (not a subdirectory)
            if os.path.isfile(file_path):
                # Print the file name before deletion
                click.echo(f"Deleting: {file_name}")

                # Uncomment the following line to delete the file
                os.remove(file_path)
    else:
        click.echo("Directory does not exist or is not a directory:", CACHE_PATH)


def courses_to_take(format):
    schedule = get_semester_schedule()
    courses = get_courses()
    grades = get_grades()
    # completed_courses_list=grades["ID"].tolist()

    # print(courses[courses["DEPENDENCIES"].fillna("").str.contains("[(|)|{|}|ή|και]",regex=True)])

    click.echo("QoL changes:", err=True)

    click.echo("+ Removed E* courses where you have >=3 .", err=True)

    completed_courses = pd.merge(
        courses.drop(columns=["NAME"]), grades, on=["ECTS", "ID"], how="right"
    )
    completed_courses["TYPE"] = completed_courses["TYPE"].fillna(CourseType.FREE.name)

    non_completed = schedule[~schedule["ID"].isin(completed_courses["ID"])]
    desired_types = ["E3", "E4", "E5", "E6", "E7", "E8", "E9"]
    type_counts = completed_courses["TYPE"][
        completed_courses["TYPE"].isin(desired_types)
    ].value_counts()
    exceeded_number_of_type = type_counts[type_counts >= 3].index.tolist()
    available_courses = pd.merge(
        courses.drop(columns=["RECOMMENDED", "NAME"]),
        non_completed,
        on=["ID"],
        how="inner",
    )
    available_courses = available_courses[
        ~available_courses["TYPE"].isin(exceeded_number_of_type)
    ]

    click.echo("+ Removed courses that you have completed.", err=True)
    click.echo(
        "- Removed courses where you dont have dependencies completed. [ DISABLED ]",
        err=True,
    )

    # click.echo("+ Removed courses where you dont have dependencies completed. [ BUGGY ! ]")

    # unsafe_pattern = re.compile(r"[(|)|{|}|ή|και]")
    # print(available_courses[available_courses["DEPENDENCIES"].fillna("").str.contains("[(|)|{|}|ή|και]",regex=True)])

    # def split_deps_safe(deps:str):
    #     unsafe = unsafe_pattern.search(deps)
    #     if unsafe :
    #         return deps
    #     return [ id.strip() for id in deps.split(",") ]
    #
    #
    # available_courses["DEPENDENCIES"]=available_courses["DEPENDENCIES"].astype(str).apply(split_deps_safe)
    # def check_strings_in_list(lst):
    #
    #     return all(item in completed_courses_list for item in lst)
    # print(available_courses)
    # print(available_courses[available_courses["DEPENDENCIES"].apply(check_strings_in_list)])
    # print(available_courses)

    if format == "csv":
        print(available_courses.to_csv(sep="|",index=False,encoding="utf-8"))
    elif format == "md":
        print(available_courses.to_markdown())
    elif format == "json":
        print(available_courses.to_json(force_ascii=False))
    elif format == "pretty":
        print(available_courses)
        print("\nCheck `courses --help for more usefull formats`")
    elif format == "pdf":
        assert False, "Not implemented"


def check_degree_completion():
    def check(contition: bool):
        return (
            click.style("PASS", bold=True, fg="green")
            if contition
            else click.style("NOT YET", bold=True, fg="yellow")
        )

    def head_sep():
        click.secho("=" * 68, bold=True)

    def sep():
        click.secho("-" * 40, bold=True)

    def pad(depth: int):
        return " " * 4 * depth

    def print_table(depth: int, courses: pd.DataFrame, cols: list):
        text_courses = ["NONE"]
        if not courses.empty:
            text_courses = (
                courses[cols].to_string(index=False, justify="left").splitlines()
            )
        click.echo(pad(depth) + click.style(text_courses[0], bold=True))
        for course in text_courses[1:]:
            click.echo(pad(depth) + course)
        click.echo()

    important_cols = ["ECTS", "ID", "NAME"]
    courses = get_courses()
    grades = get_grades()

    completed_courses = pd.merge(
        courses.drop(columns=["NAME"]), grades, on=["ECTS", "ID"], how="right"
    )
    completed_courses["TYPE"] = completed_courses["TYPE"].fillna(CourseType.FREE.name)

    head_sep()
    click.echo()

    click.echo(f"{click.style('[1]',bold=True)} At least 8 semesters :")
    sep()
    click.echo("LOL, ok buddy...")
    click.echo()

    click.echo(f"{click.style('[2]',bold=True)} All BASE courses :")
    sep()
    click.echo(
        "These are the missing BASE courses you need to complete the requirements."
    )
    click.echo()
    base_courses = courses[courses["TYPE"] == "BASE"]
    completed_base_courses = completed_courses[completed_courses["TYPE"] == "BASE"]
    missing_base_courses = base_courses[
        ~base_courses["ID"].isin(completed_base_courses["ID"])
    ]
    print_table(1, missing_base_courses, ["TYPE", "ID", "NAME", "ECTS", "DEPENDENCIES"])

    click.echo(f"{click.style('[3]',bold=True)} 20 ECTS from E1>=2 or E2<=1 :")
    sep()
    completed_E1E2_courses = completed_courses[
        (completed_courses["TYPE"] == "E1") | (completed_courses["TYPE"] == "E2")
    ]

    # click.echo(completed_E1E2_courses)
    E1 = completed_E1E2_courses[completed_E1E2_courses["TYPE"] == "E1"]
    E2 = completed_E1E2_courses[completed_E1E2_courses["TYPE"] == "E2"]
    E1_ects = 0 if E1.empty else E1["ECTS"].sum()
    E2_ects = 0 if E2.empty else E2["ECTS"].max()

    E1E2_ects = E1_ects + E2_ects
    click.echo()
    click.echo("You need at least 2 E1 courses passed.")
    click.echo(
        f"{pad(1)}{ click.style('E1',bold=True) }: {len(E1)} passed courses ({E1_ects})"
    )
    click.echo()
    print_table(2, E1, important_cols)
    click.echo()
    click.echo("You need at most 1 E2 courses passed.(If more than 1 the max is taken)")
    click.echo(
        f"{pad(1)}{ click.style('E2',bold=True) }: {len(E2)} passed courses ({E2_ects})"
    )
    click.echo()
    print_table(2, E2, important_cols)

    click.echo(
        f"You have {click.style(E1E2_ects,bold=True)} out of 20: { check(E1E2_ects>=20) }"
    )
    click.echo()

    click.echo(f"{click.style('[4]',bold=True)} E3-E9 Courses :")
    sep()
    # completed_courses[]

    desired_types = ["E3", "E4", "E5", "E6", "E7", "E8", "E9"]
    completed_E3toE9_courses = completed_courses[
        completed_courses["TYPE"].isin(desired_types)
    ]

    # def sum_of_3_largest(group):
    #     return group.nlargest(3, "ECTS")["ECTS"].sum()

    def sum_of_3_largest(group):
        largest_values = group.nlargest(3, "ECTS")
        sum_of_largest = largest_values["ECTS"].sum()
        selected_values = largest_values["ID"].tolist()
        return pd.Series(
            [sum_of_largest, selected_values],
            index=["Sum_of_3_Largest", "Selected_Courses"],
        )

    # Group by 'TYPE' and apply the sum_of_3_largest function
    result = (
        completed_E3toE9_courses.groupby("TYPE").apply(sum_of_3_largest,include_groups=False).reset_index()
    )
    print_table(1, result, ["TYPE", "Sum_of_3_Largest", "Selected_Courses"])
    E3toE9_ects = result["Sum_of_3_Largest"].sum()
    click.echo()
    click.echo(
        f"You have {click.style(E3toE9_ects,bold=True)} out of 42: { check(E3toE9_ects>=42) }"
    )
    click.echo()

    click.echo(f"{click.style('[5]',bold=True)} One FREE course or n>3 E3-E9 Courses :")
    sep()
    print_table(
        1,
        completed_courses[completed_courses["TYPE"] == "FREE"][important_cols],
        important_cols,
    )

    click.echo(f"{click.style('[6]',bold=True)} 240 ECTS :")
    sep()
    all_ects = completed_courses["ECTS"].sum()
    click.echo(
        f"{pad(1)}{click.style('ECTS',bold=True)}: {all_ects} out of 240  {check(all_ects>=240)}"
    )


def get_grades(ignore_cache: bool = False) -> pd.DataFrame:
    if not os.path.exists(GRADES_CACHE) or ignore_cache:
        click.echo("Please wait while we fetch your grades...")
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
    with open(SCEDULE_CACHE, "w", encoding="utf-8") as schedule_cache:
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
        click.echo(f"Downloaded: {path}",err=True)
    else:
        click.echo(f"Failed to download: {url}",err=True)


def get_courses(ignore_cache: bool = False) -> pd.DataFrame:
    if not os.path.exists(COURSE_CACHE) or ignore_cache:
        fetch_courses()

    df = pd.read_csv(COURSE_CACHE, delimiter="|", index_col=False)
    df["ECTS"] = pd.to_numeric(df["ECTS"], errors="coerce")
    return df


def fetch_grades() -> None:
    try:
        options = webdriver.FirefoxOptions()
        options.add_argument("-headless")
        driver = webdriver.Firefox(options=options)
    except Exception:
        print("Only Firefox Officially Supported for now, will try Chrome...")
        try:
            options = webdriver.ChromeOptions()
            options.add_argument("--headless")
            driver = webdriver.Chrome(options=options)
        except Exception as e:
            print("Chrome failed as well...exiting")
            raise e

    email, password = get_credentials()

    driver.get(
        "https://sso.uoc.gr/login?service=https%3A%2F%2Feduportal.cict.uoc.gr%2Flogin%2Fcas"
    )

    driver.implicitly_wait(1)
    try:
        if driver.find_element(BY.CSS_SELECTOR, "#notfound"):
            print("Eduportal is Down AGAIN LOL!")
            exit(1)
    except NoSuchElementException:
        pass

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

    try:
        grades_element = wait.until(EC.presence_of_element_located(grades))
    except TimeoutException as e:
        print("Eduportal must be down AGAIN, check the site https://eduportal.cict.uoc.gr/ ")
        exit(1)

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

    with open(GRADES_CACHE, "w", encoding="utf-8") as grades_cache:
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
    with open(COURSE_CACHE, "w", encoding="utf-8") as courses:
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
    am = input("AM (eg 4438): ")
    username = f"csd{am}@csd.uoc.gr"

    password = pwinput.pwinput(prompt="Password (hidden): ", mask="*")
    return username, password


def get_courses_completions():
    pass


if __name__ == "__main__":
    init()
    cli()
