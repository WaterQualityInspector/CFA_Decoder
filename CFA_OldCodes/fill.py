from selenium import webdriver
from contextlib import contextmanager
from selenium.webdriver.support.expected_conditions import \
    staleness_of
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException
import time
from os import path
import re
from random import choices, randint, choice


##******************** CONSTANTS ********************##
EMAIL_FILE_NAME = "Scott_Emails.txt"
DEMOGRAPHIC_CHOICES = {
    "R00105": [[6, 3, 2, 4, 9], [7, 2, 2, 1.5, 1]],
    "R00105": [[1, 2, 3, 4, 5, 6, 7, 8, 9], [1, 2, 3, 4, 5, 3, 2, 1, 4]],
    "R00103": [[1, 2, 3, 4, 5, 6, 9], [1, 3, 5, 5, 4, 3, 2]],
    "R00102": [[1, 2, 9], [5, 5, 2]]
}
##***************************************************##


def google_logon(driver):
    email = "PaulaAndy45@gmail.com"
    psw = "ja9p0oorLFHlIdcQLkPLLhW7vso6r2Ix"
    
    recovery_email = "dimensionalsquirrel@gmail.com"

    driver.get("https://accounts.google.com/signin")
    email_phone = driver.find_element_by_xpath("//input[@id='identifierId']")
    email_phone.send_keys(email)
    driver.find_element_by_id("identifierNext").click()
    WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, "//input[@name='password']")))
    password = driver.find_element_by_xpath("//input[@name='password']")
    password.send_keys(psw)
    driver.find_element_by_id("passwordNext").click()
    
    time.sleep(1.5)
    url = driver.current_url
    if 'https://accounts.google.com/signin/v2/challenge' in url:
        try:
            el = driver.find_element_by_xpath("//div[contains(text(), 'Confirm your recovery email')]")
            el.click()
        except Exception as e:
            input("Enter to break")
            raise(e)
        
        email_entry = driver.find_element_by_xpath("//input[@type='email']")
        email_entry.send_keys(recovery_email)
        
        driver.find_element_by_xpath("//span[contains(text(), 'Next')]").click()
    
    return driver.get_cookies()


def nav_to_cfa(driver):
    driver.get("http://www.mycfavisit.com")
    with open(path.join("Raw_Codes", "Unused_codes.csv")) as f:
        code = f.readline()[:-1].split(',')
    
    if len(code) < 3:
        raise ValueError("No codes left to check")
    
    WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, "//input[@name='CN1']")))
    for id, keys in zip(["CN1", "CN2", "CN3", "CN4", "CN5"], code):
        el = driver.find_element_by_id(id)
        el.send_keys(keys)
    try:
        driver.find_element_by_id("NextButton").click()
    except ElementClickInterceptedException:
        with wait_for_recaptcha_completion(driver):
            driver.find_element_by_id("NextButton").click()
    return code

    
def parse_website(driver, emails=None):
    done = True
    if re.search(r'(?<!FNS)(S\d{5})(?!(?:\|R\d{5})+?)', driver.page_source) is not None:
        if emails is not None:
            random_email = choice(emails)
            completed_matches = []
            for match in re.findall(r'(?<!FNS)(S\d{5})(?!(?:\|R\d{5})+?)', driver.page_source):
                if match in ["S93000", "S93500"] and match not in completed_matches:
                    completed_matches.append(match)
                    WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, f"//input[@id='{match}']")))
                    text_input = driver.find_element_by_xpath(f"//input[@id='{match}']")
                    try:
                        text_input.click()
                        text_input.send_keys(random_email)
                    except ElementClickInterceptedException:
                        with wait_for_recaptcha_completion(driver):
                            text_input.click()
                            text_input.send_keys(random_email)
        done = False
        with wait_for_page_load(driver):
            print("Enter your response into the box and press the next button.")
            return False
    
    elif re.search(r'R\d{5}.*?(R\d{5}\.)\d', driver.page_source) is not None:
        checked_matches = []
        for match in re.findall(r'R\d{5}.*?(R\d{5}\.)\d', driver.page_source, flags=(re.ASCII | re.DOTALL)):
            done = False
            if match in checked_matches:
                continue
            checked_matches.append(match)
            if re.search(match + "5", driver.page_source) is not None:
                button_choice = choices([3,4,5], [1, 5, 8])
                click_element = str(button_choice[0])
            elif re.search(match + "2", driver.page_source) is not None:
                if match != "R18000.":
                    click_element = "2"
                else:
                    click_element = "1"
            else:
                with wait_for_page_load(driver):
                    print("No clickable element found. Navigate onto the next page to continue")
                    return False
            WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, f"//input[@id='{match + click_element}']/../span")))
            try:
                driver.find_element_by_xpath(f"//input[@id='{match + click_element}']/../span").click()
            except ElementClickInterceptedException:
                with wait_for_recaptcha_completion(driver):
                    driver.find_element_by_xpath(f"//input[@id='{match + click_element}']/../span").click()
            
    elif "What did you personally eat on this visit" in driver.page_source:
        checked_matches = []
        for match in re.findall(r'(FNSR\d{5})" class="cataOption"', driver.page_source, flags=(re.ASCII | re.DOTALL)):
            done = False
            if match in checked_matches or match == "FNSR00435" or match == "FNSR00431":
                continue
            checked_matches.append(match)
            WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, f"//div[@id='{match}']/span/span")))
            try:
                driver.find_element_by_xpath(f"//div[@id='{match}']/span/span").click()
            except ElementClickInterceptedException:
                with wait_for_recaptcha_completion(driver):
                    driver.find_element_by_xpath(f"//div[@id='{match}']/span/span").click()
    
    elif "Including this visit, how many times" in driver.page_source:
        first_choice = randint(1, 10)
        for n, match in enumerate(re.findall(r'select id="(R\d{5})" name="\1"', driver.page_source, flags=(re.ASCII | re.DOTALL))):
            done = False
            WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, f"//select[@id='{match}']")))
            button = driver.find_element_by_xpath(f"//select[@id='{match}']")
            if n == 0:
                try:
                    Select(button).select_by_value(str(first_choice))
                except ElementClickInterceptedException:
                    with wait_for_recaptcha_completion(driver):
                        Select(button).select_by_value(str(first_choice))
            else:
                try:
                    Select(button).select_by_value(str(randint(first_choice, 10)))
                except ElementClickInterceptedException:
                    with wait_for_recaptcha_completion(driver):
                        Select(button).select_by_value(str(randint(first_choice, 10)))
    
    elif "Please select your gender" in driver.page_source:
        for match in re.findall(r'select id="(R\d{5})" name="\1"', driver.page_source, flags=(re.ASCII | re.DOTALL)):
            done = False
            if match not in DEMOGRAPHIC_CHOICES:
                input("Select code not found in demographic choices list, please press enter to continue")
            options, weights = DEMOGRAPHIC_CHOICES[match]
            selection = choices(options, weights)
            WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, f"//select[@id='{match}']")))
            button = driver.find_element_by_xpath(f"//select[@id='{match}']")
            try:
                Select(button).select_by_value(str(selection))
            except ElementClickInterceptedException:
                with wait_for_recaptcha_completion(driver):
                    Select(button).select_by_value(str(selection))
    
    elif "You will receive an email within 24 hours" in driver.page_source:
        print("Final page found, exiting.")
        return True
    
    try:
        WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, f"//input[@id='NextButton']")))
        try:
            driver.find_element_by_id("NextButton").click()
        except ElementClickInterceptedException:
            with wait_for_recaptcha_completion(driver):
                driver.find_element_by_id("NextButton").click()
        return done
    except TimeoutException:
        print("Button not found, exiting")
        return True

@contextmanager
def wait_for_page_load(driver, timeout=600):
    old_page = driver.find_element_by_tag_name('html')
    yield WebDriverWait(driver, timeout).until(staleness_of(old_page))


@contextmanager
def wait_for_recaptcha_completion(driver, timeout=600):
    old_page = driver.find_element_by_xpath("//div[@id='challenge-dialog']")
    yield WebDriverWait(driver, timeout).until(staleness_of(old_page))

    
if __name__ == "__main__":
    with open(path.join("Raw_Codes", "Unused_codes.csv"), 'r') as fin:
        if len(fin.read()) < 5:
            raise ValueError("No codes to read. Enter them into the unused codes file or run scotts_work.py for codes.")
    try:
        options = webdriver.ChromeOptions()
        options.add_argument('log-level=3')
        driver = webdriver.Chrome(options=options)
        saved_cookies = google_logon(driver)
        repeat = True
        loaded_emails = []
        with open(path.join("Email_Files", EMAIL_FILE_NAME)) as f:
            for line in f:
                loaded_emails.append(line[:-1])
        while repeat:
            current_code = nav_to_cfa(driver)
            if "already been completed" in driver.page_source:
                print("Code has already been used. Deleting code and restarting survey.")
                with open(path.join("Raw_Codes", "Unused_codes.csv"), 'r') as fin:
                    data = fin.read().splitlines(True)
                with open(path.join("Raw_Codes", "Unused_codes.csv"), 'w') as fout:
                    fout.writelines(data[1:])
                continue
            print(f"Working on code: {current_code}")
            finished = False
            while not finished:
                finished = parse_website(driver, emails=loaded_emails)
                # if finished:
                #     finished = input("Keep going (enter 'yes' to continue)?: ") != "yes"
            if input("Delete code used (enter 'no' to save)? ") != 'no':
                with open(path.join("Raw_Codes", "Unused_codes.csv"), 'r') as fin:
                    data = fin.read().splitlines(True)
                with open(path.join("Raw_Codes", "Unused_codes.csv"), 'w') as fout:
                    fout.writelines(data[1:])
            driver.delete_all_cookies()
            for cookie in saved_cookies:
                if 'expiry' in cookie:
                    cookie['expiry'] = int(cookie['expiry'])
            repeat = 'y' in input("Complete another survey (enter 'y' to continue)? ")
        input("Close the browser or press enter to quit the program")
    finally:
        driver.close()
        driver.quit()
