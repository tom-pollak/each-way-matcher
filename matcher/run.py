import os
import sys
import traceback
from datetime import datetime
from time import sleep
from dotenv import load_dotenv
from selenium import webdriver

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException

from .odds_monkey import scrape

BASEDIR = os.path.abspath(os.path.dirname(__file__) + '/../')
load_dotenv(os.path.join(BASEDIR, '.env'))

ODD_M_USER = os.environ.get('ODD_M_USER')
ODD_M_PASS = os.environ.get('ODD_M_PASS')
S_INDEX_USER = os.environ.get('S_INDEX_USER')
S_INDEX_PASS = os.environ.get('S_INDEX_PASS')


def login(driver):
    driver.get('https://www.oddsmonkey.com/oddsmonkeyLogin.aspx?returnurl=%2f')
    try:
        WebDriverWait(driver, 60).until(
            EC.visibility_of_element_located(
                (By.ID, 'dnn_ctr433_Login_Login_DNN_txtUsername'
                 ))).send_keys(ODD_M_USER)
    except TimeoutException:
        raise ValueError("Couldn't login to Oddsmonkey")
    driver.find_element_by_id(
        'dnn_ctr433_Login_Login_DNN_txtPassword').send_keys(ODD_M_PASS)
    driver.find_element_by_id('dnn_ctr433_Login_Login_DNN_cmdLogin').click()
    sleep(2)

    driver.get('https://www.oddsmonkey.com/Tools/Matchers/EachwayMatcher.aspx')
    try:
        WebDriverWait(driver, 60).until(
            EC.element_to_be_clickable(
                (By.XPATH,
                 '//*[@id="dnn_ctr1157_View_RadGrid1_ctl00"]/thead/tr/th[17]/a'
                 ))).click()
    except TimeoutException:
        print('Need Oddsmonkey premium membership (OM12FOR1)')
        sys.exit()
    except ElementClickInterceptedException:
        print("Dismiss one time pop-up boxes and setup oddsmonkey")
        sys.exit()

    driver.execute_script(
        '''window.open("https://www.sportingindex.com/fixed-odds","_blank");'''
    )
    sleep(2)

    driver.switch_to.window(driver.window_handles[1])
    try:
        WebDriverWait(driver, 60).until(
            EC.visibility_of_element_located(
                (By.ID, 'usernameCompact'))).send_keys(S_INDEX_USER)
    except TimeoutException:
        raise ValueError("Couldn't login to Sporting Index")
    driver.find_element_by_id('passwordCompact').send_keys(S_INDEX_PASS)
    driver.find_element_by_id('submitLogin').click()
    sleep(5)
    print('Logged in')
    sys.stdout.flush()


def run_matcher():
    if None in (ODD_M_USER, ODD_M_PASS, S_INDEX_USER, S_INDEX_PASS):
        raise Exception(
            'ERROR: SportingIndex or Oddsmonkey env variables not set')

    if not os.path.isfile('client-2048.crt') or not os.path.isfile(
            'client-2048.key'):
        raise Exception('client-2048 certificates not found')

    print(f'Started at: {datetime.now().strftime("%H:%M:%S %d/%m/%Y")}')
    while True:
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (X11; CrOS x86_64 8172.45.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.64 Safari/537.36"
        )
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-setuid-sandbox")
        chrome_options.add_argument("--remote-debugging-port=9222")  # this
        chrome_options.add_argument("--disable-dev-shm-using")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("start-maximized")
        prefs = {"profile.default_content_setting_values.notifications": 2}
        chrome_options.add_experimental_option("prefs", prefs)
        driver = webdriver.Chrome(options=chrome_options)
        sys.stdout.flush()
        try:
            login(driver)
            scrape(driver)
        except ValueError as e:
            sys.stdout.flush()
            print('ERROR: %s\n' % e)
        except KeyboardInterrupt:
            sys.stdout.flush()
            print('Exiting')
            sys.exit()
        except Exception as e:
            sys.stdout.flush()
            print('Error occured: %s' % e)
            print(traceback.format_exc())
        finally:
            driver.quit()
