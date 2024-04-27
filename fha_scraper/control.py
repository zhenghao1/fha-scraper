import logging
from pathlib import Path
from typing import List
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException
import os
import time

import tenacity

from .csv import generate_country_csv

logging.basicConfig(level=logging.DEBUG)

DRIVER_PATH = '/usr/bin/chromedriver'
SAVED_FILES_PATH = os.environ.get('FHA_FILE_PATH', Path.home().joinpath("fha_files").as_posix())
service = webdriver.ChromeService(executable_path=DRIVER_PATH)
options = webdriver.ChromeOptions()

options.page_load_strategy = 'normal'
options.add_argument("--start-maximized")
options.add_experimental_option("detach", True)

driver = webdriver.Chrome(options=options, service=service)

def main():
    """
    A function that performs some action using the Selenium WebDriver.

    This function navigates to a specific URL and retrieves the HTML source code of the page. 
    It then prints the source code to the console.

    Parameters:
    None

    Returns:
    None
    """
    logging.info("Browsing to https://event.fhafnb.com/...")
    driver.get("https://event.fhafnb.com/")
    login()
    logging.info("Successfully logged in")
    meet()
    search_contries()
    

# Login to website
def login():
    """
    Logs into the website using the provided password from the environment variable 'FHA_PASSWORD'.

    This function waits for the password field to be present on the page and then fills in the password and clicks the submit button.

    Parameters:
    None

    Returns:
    None

    Raises:
    Exception: If the environment variable 'FHA_PASSWORD' is not set.
    """
    password_field = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="passcode_login"]/input'))
    )
    password_submit_button = driver.find_element(By.ID, "passcode_start")
    if (password := os.environ.get("FHA_PASSWORD")) is None:
        logging.error("FHA_PASSWORD environment variable is not set")
        raise Exception("Please set the environment variable 'FHA_PASSWORD' to your password")
    password_field.send_keys(password)
    password_submit_button.click()

# Click on meet tab to search for people
def meet():
    """
    Attempts to find and click the handshake menu element using Selenium WebDriver. 
    If the handshake menu is visible, it clicks the close button and prints a message. 
    If the handshake menu is not visible, it prints a message indicating that. 
    
    Parameters:
    None
    
    Returns:
    None
    """
    try:
        handshake_menu = WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.XPATH, '//*[@id="handshake_menu"]')))
        driver.find_element(By.XPATH, '//*[@id="icon_close"]').click()
        logging.info("Handshake menu is visible")
    except:
        logging.info("Handshake menu is not visible")
    meet_element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="select_profs_desk"]'))
    )
    meet_element.click()

# Get list of countries from FHA
def get_country_elements() -> List[WebElement]:
    """
    A function that retrieves a list of country elements from the web page.
    
    Returns:
        List[WebElement]: A list of country elements.
    """
    country_elements = driver.find_elements(By.CSS_SELECTOR, '#dd_search_1 > div')
    return country_elements

def search_contries():
    """
    This function searches for countries using Selenium WebDriver.
    
    Parameters:
    None
    
    Returns:
    None
    """
    time.sleep(0.5)
    app_banner = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, 'div.inapp_banner'))
    )
    country_dropdown = driver.find_element(By.XPATH, '//*[@id="s_drops"]/div[2]/div')
    people_subfilter = driver.find_element(By.XPATH, '//*[@id="view_peo"]')
    attendee_subfilter = driver.find_element(By.ID, "grp_dd_sel")
    attendee_select = Select(attendee_subfilter)

    country_elements = get_country_elements()
    previous = None
    current = None
    i = 0
    while i < len(country_elements):

        # Take a 5 second break every 5 countries processed
        if i%5 > 0:
            time.sleep(5)

        # Open country selection
        ActionChains(driver).move_to_element(app_banner).click(country_dropdown).perform()

        # If previously a country was already selected
        # unselect it by clicking it to uncheck the checkmark
        if previous is not None:
            previous_country = previous.get_attribute('data-dd-search-val')
            previous_element = wait_for_country_element(30, previous_country)
            click_country(previous_element)
            logging.debug("De-select previous country: %s", previous_country)
        elif i != 0 and previous is None:
            print("Previous is none!")
            raise Exception("Previous country element is NONE!")

        # Set the current country
        current = country_elements[i]
        current_country = current.get_attribute('data-dd-search-val')
        current_element = wait_for_country_element(30, current_country)
        click_country(current_element)
        logging.debug("Selecing current country: %s", current_country)

        # Click on search button in country dropdown selection
        driver.find_element(By.XPATH, '//div[@id="dd_menu_foot"]/button[2]').click()
        logging.debug("Search for records in country: %s", current_country)
        
        # Give it time to load the data
        time.sleep(3)

        people_subfilter.click()
        attendee_select.select_by_visible_text('Visitor')

        time.sleep(0.5)

        if(has_data()):
            infinite_scroll()
            attendee_html = get_attendee_list_html()
            csv_filename = f'{SAVED_FILES_PATH}/{current_country.upper()}.csv'
            generate_country_csv(attendee_html, csv_filename)
            # Do something to get the dom tree
        i += 1
        previous = current

def click_country(element: WebElement) -> None:
    """
    Clicks on a previous country element.

    Args:
        element (WebElement): The previous country element to click on.

    Returns:
        None
    """
    if element.is_displayed():
        element.click()
    else:
        driver.execute_script("arguments[0].scrollIntoView(true);", element)
        element.click()
        

def infinite_scroll():
    """
    Scroll down until no more new data is available.

    This function uses the Selenium WebDriver to scroll down the page until no more new data is loaded. It does this by repeatedly executing a JavaScript script to scroll to the bottom of the page and then checking if the page height has changed. If the page height has not changed after scrolling, it means that there is no more new data and the function stops scrolling.

    Parameters:
    None

    Returns:
    None
    """
    # Scroll down until no more new data
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2.5)  # Wait to load content
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

def has_data() -> bool:
    """
    A function that checks if there is data available based on the results text.

    Returns:
        bool: True if there is data, False otherwise.
    """
    results = driver.find_element(By.ID, 'list_top_in').text
    if results.startswith('No results.'):
        return False
    else:
        return True

def quit():
    driver.quit()

element_retry = tenacity.retry(
    stop=tenacity.stop_after_attempt(3),
    retry=tenacity.retry_if_exception_type(TimeoutException),
    reraise=True
)

@element_retry
def wait_for_country_element(seconds: float, country: str):
    """
    A function that waits for and returns a specific country element based on the country name and a specified time limit.

    Parameters:
        seconds (float): The time limit in seconds to wait for the element.
        country (str): The name of the country to search for.

    Returns:
        WebElement: The WebElement corresponding to the country element.
    """
    element = WebDriverWait(driver, seconds).until(
        EC.visibility_of_element_located((By.XPATH, '//*[@id="dd_search_1"]/div[@data-dd-search-val="' + country  + '"]'))
    )
    return element

def get_attendee_list_html() -> str:
    """
    A function that returns the HTML content of the attendee unordered list.

    Returns:
        str: The HTML content of the attendee unordered list.
    """
    attendee_element = WebDriverWait(driver, 30).until(
        EC.visibility_of_element_located((By.ID, 'attendees'))
    )
    if attendee_element.is_displayed():
        return attendee_element.get_attribute('outerHTML')
    else:
        return '<ul id="attendees"></ul>'

if __name__ == '__main__':
    main()