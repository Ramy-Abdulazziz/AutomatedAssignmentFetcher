
from datetime import datetime, timedelta
from selenium import webdriver
from bs4 import BeautifulSoup as bs
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from multiprocessing import Process, Manager
from CalendarAPI.cal_setup import get_calendar_service as cs
from Notifications.notify import send_email as se
import CalendarAPI.google_api_helper as gh
import time
import json as js


def filter_assignment_name_date(tag: bs):
    return tag.name == 'th' and tag.has_attr('class') and 'd2l-table-cell-first' in tag['class']


# return (tag.name == 'tr' and not tag.has_attr('class')) or ((tag.has_attr('class'))
#                                                             and (('d2l-table-cell-first' in tag['class']) ^ ('d2l-table-cell-last' in tag['class'])))


def filter_correct_rows(tag: bs):

    return not tag.has_attr('class') or ((tag.has_attr('class')
                                          and (('d2l-table-cell-first' in tag['class']) ^ ('d2l-table-cell-last' in tag['class']))))


def init_driver():

    chrome_options = Options()
    service_loc = Service(
        r'C:\\Users\\ramya\\python-scripts\\AssignmentFetcher\\Drivers\\chromedriver.exe')
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-web-security')
    chrome_options.add_argument('log-level=3')
    chrome_options.add_experimental_option(
        'excludeSwitches', ['enable-logging'])
    chrome_options.binary_location = r"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"

    driver = webdriver.Chrome(service=service_loc, options=chrome_options)

    return driver


def get_user_login_details():

    with open("AssignmentFetcher/Credentials/login-details.json", "r") as login:

        login_details = js.load(login)

    login_details = login_details.get("StonyBrook-Brightspace")

    user_name = login_details.get("username")
    pswrd = login_details.get("password")

    login_info = {'user_name': user_name, 'pswrd': pswrd}

    return login_info


def get_course_assign_pages():

    with open("AssignmentFetcher/URLPaths/assignment_page_url.json", "r") as pages:

        urls = js.load(pages)

    return urls


def log_in_sbu(driver, user_name, pswrd):

    driver.get("https://mycourses.stonybrook.edu/d2l/home")

    log_button_parent = driver.find_element(
        by=By.TAG_NAME, value="d2l-html-block")

    shadow_content = log_button_parent.shadow_root

    sbu_log_in = shadow_content.find_element(
        by=By.CSS_SELECTOR, value="p > a > img")

    sbu_log_in.click()

    user_name_field = driver.find_element(by=By.ID, value="username")
    pass_field = driver.find_element(by=By.ID, value="password")

    user_name_field.send_keys(user_name)
    pass_field.send_keys(pswrd)

    submit_button = driver.find_element(
        by=By.CLASS_NAME, value="login-button")

    submit_button.click()


def authenticate_duo(driver):

    driver.switch_to.frame(driver.find_element(
        by=By.TAG_NAME, value="iframe"))

    WebDriverWait(driver, 60).until(
        EC.element_to_be_clickable(((By.CLASS_NAME, 'auth-button'))))
    WebDriverWait(driver, 60, 3).until(
        EC.presence_of_element_located((By.CLASS_NAME, 'auth-button')))
    send_push = driver.find_element(by=By.CLASS_NAME, value="auth-button")

    send_push.click()

    print('Open Duo to Authenticate Log In Request within 60 seconds ')


def get_assignment_table_and_course_details(driver, course_assign_page):

    WebDriverWait(driver, 60, 3).until(
        EC.presence_of_element_located((By.CLASS_NAME, 'd2l-homepage')))

    driver.get(course_assign_page)

    assignment_page = driver.page_source

    assign_soup = bs(assignment_page, "html.parser")

    try:
        class_name = assign_soup.head.title.text
        class_name = class_name.split("-")[2]

        class_num = class_name[0:7]
        class_title = class_name[11:]
    except IndexError:
        print('Error with Duo Authentication - Try Again')
        exit()

    assign_table = assign_soup.body.table
    rows = assign_table('tr')

    print(f"Finding assignments for {class_num} - {class_title}")

    return (class_num, class_title, rows)


def get_assignment_details(rows):

    assignments = dict()

    # for row in rows:

    #     good_rows = row(filter_assignment_name_date)

    #     assignment_name = None
    #     due_date = None

    #     for gr in good_rows:
    #         name = gr.find('a')
    #         date = gr.find('label')

    #         if name is not None:
    #             assignment_name = name.text
    #         if date is not None:
    #             due_date = date.text

    #     if (assignment_name is not None) and (due_date is not None):
    #         assignments[assignment_name] = due_date
    for row in rows:
        name_tag = row.find('a', class_='d2l-link d2l-link-inline')
        date_tag = row.find('label')

        if name_tag and date_tag:
            assignment_name = name_tag.text.strip()
            due_date = date_tag.text.replace("Due on ", "").strip()
            assignments[assignment_name] = due_date

    return assignments


def add_assignments_to_calendar(assignments: dict, class_title, class_num):

    for key in assignments:
        time = assignments[key].replace("Due on ", "")
        time_orig_format = datetime.strptime(time, "%b %d, %Y %I:%M %p")
        current_date = datetime.now()

        if time_orig_format >= current_date:

            end_time = datetime.strftime(
                time_orig_format, '%Y-%m-%dT%H:%M:%S.00-04:00')
            start_time = time_orig_format - timedelta(minutes=30)
            start_time = datetime.strftime(
                start_time, '%Y-%m-%dT%H:%M:%S.00-04:00')

            event_list = gh.check_if_event_exisits(start_time, end_time)

            if (len(event_list['items']) == 0) or (not event_list['items'][0]['summary'] == f"{class_num} - {key}"):

                gh.add_event(f"{class_num} - {key}",
                             f"{class_title} {key} due {assignments[key]}", start_time, end_time)

                print(
                    f"added {class_num} - {key} to calendar and is due {assignments[key]}")


def get_assignments(manager_dict: dict, course_page):

    driver = init_driver()
    login: dict = get_user_login_details()

    log_in_sbu(driver, login.get('user_name'), login.get('pswrd'))
    authenticate_duo(driver)

    (class_num, class_title, rows) = get_assignment_table_and_course_details(
        driver, course_page)

    assignments = get_assignment_details(rows)
    # manager_dict.update(assignments)

    add_assignments_to_calendar(assignments, class_title, class_num)


if __name__ == "__main__":

    manager = Manager()
    shared_dict = manager.dict()

    urls = get_course_assign_pages()

    # print("Sending notification text")
    # se()
    # time.sleep(10)

    for key in urls:

        get_assignments(shared_dict, urls[key])
    #     p = Process(target=get_assignments, args=(shared_dict, urls[key]))
    #     p.start()

    # p.join()
