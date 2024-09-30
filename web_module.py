import asyncio
from selenium import webdriver
from selenium.common import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as EC
import re


def setup_firefox_with_proxy(proxy=None):
    # Configure Firefox options
    firefox_options = Options()
    firefox_options.binary_location = r'C:\Program Files\Mozilla Firefox\firefox.exe'

    # If you want to run in headless mode (without opening the browser window), uncomment the line below
    #firefox_options.add_argument("--headless")

    # Set up the proxy (if provided)
    if proxy:
        # Parse the proxy format (e.g., socks4://ipaddress:port)
        proxy_pattern = re.match(r'(http|https|socks4|socks5)://([\w.]+):(\d+)', proxy)
        if proxy_pattern:
            protocol, ip, port = proxy_pattern.groups()

            if protocol.startswith('socks'):
                # SOCKS proxy configuration for Firefox
                firefox_options.set_preference('network.proxy.type', 1)  # Use manual proxy configuration
                firefox_options.set_preference('network.proxy.socks', ip)  # Proxy IP
                firefox_options.set_preference('network.proxy.socks_port', int(port))  # Proxy Port

                if protocol == 'socks5':
                    firefox_options.set_preference('network.proxy.socks_version', 5)  # Use SOCKS5
                else:
                    firefox_options.set_preference('network.proxy.socks_version', 4)  # Use SOCKS4
            else:
                # HTTP/HTTPS proxy configuration
                firefox_options.set_preference('network.proxy.type', 1)  # Use manual proxy configuration
                firefox_options.set_preference('network.proxy.http', ip)  # Proxy IP
                firefox_options.set_preference('network.proxy.http_port', int(port))  # Proxy Port
                firefox_options.set_preference('network.proxy.ssl', ip)  # Same proxy for SSL/HTTPS
                firefox_options.set_preference('network.proxy.ssl_port', int(port))  # Proxy Port

            # No proxy for local addresses
            firefox_options.set_preference('network.proxy.no_proxies_on', '')

    # Initialize the Firefox WebDriver
    service = Service(r'D:\ProgramFiles\geckodriver.exe')  # Replace with the actual path to GeckoDriver if not in PATH
    driver = webdriver.Firefox(service=service, options=firefox_options)

    return driver


def check_valid_code(driver, codes):
    try:
        # Wait for the page to load by checking if certain keywords appear in the page source
        driver.implicitly_wait(10)  # Adjust wait time as needed

        page_source = driver.page_source

        # Check if the page indicates that the code is invalid
        if 'Sorry, we are unable to continue the survey based on the information you provided.' in page_source:
            print("Invalid code.")
            return False
        # Check if the page indicates that the survey started (valid code)
        elif 'Please rate your overall satisfaction with your most recent visit' in page_source:
            print(f"Valid code: {codes}\n")
            return True
        else:
            # If neither of the above, the page might be blocked or unexpected
            raise False

    except NoSuchElementException as e:
        print(f"An error occurred while checking the page: {str(e)}")
        return False


def fill_survey_codes(driver, codes):
    # Navigate to the website
    driver.get('https://www.mycfavisit.com/')

    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "CN1")))
    except TimeoutException:
        print("Page did not load the expected content in time.")
        return False

    # Find the input fields and enter the codes
    driver.find_element(By.NAME, 'CN1').send_keys(codes[0])
    driver.find_element(By.NAME, 'CN2').send_keys(codes[1])
    driver.find_element(By.NAME, 'CN3').send_keys(codes[2])
    driver.find_element(By.NAME, 'CN4').send_keys(codes[3])
    driver.find_element(By.NAME, 'CN5').send_keys(codes[4])

    # Find and click the "Next" or "Submit" button
    driver.find_element(By.NAME, 'NextButton').click()

    # Check if the next page contains a success or failure message
    return check_valid_code(driver, codes)


def evaluate_code(codes, proxy_url):
    driver = setup_firefox_with_proxy(proxy=proxy_url)

    try:
        # Fill the survey codes and submit the form
        result = fill_survey_codes(driver, codes)

        driver.implicitly_wait(15)
        print("Form submitted!")
    finally:
        # Close the browser after everything is done
        driver.quit()

    return result


