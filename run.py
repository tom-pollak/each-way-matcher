import os
import sys
from time import time
from datetime import datetime
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException
from odds_monkey import scrape
from time import sleep

RETURNS_CSV = 'returns/returns.csv'
REFRESH_TIME = 35
START_TIME = time()
load_dotenv(dotenv_path='.env')
ODD_M_USER = os.environ.get('ODD_M_USER')
ODD_M_PASS = os.environ.get('ODD_M_PASS')
S_INDEX_USER = os.environ.get('S_INDEX_USER')
S_INDEX_PASS = os.environ.get('S_INDEX_PASS')


def login(driver, ODD_M_USER, ODD_M_PASS, S_INDEX_USER, S_INDEX_PASS):
    driver.get('https://www.oddsmonkey.com/oddsmonkeyLogin.aspx?returnurl=%2f')
    WebDriverWait(driver, 30).until(
        EC.visibility_of_element_located(
            (By.ID,
             'dnn_ctr433_Login_Login_DNN_txtUsername'))).send_keys(ODD_M_USER)
    driver.find_element_by_id(
        'dnn_ctr433_Login_Login_DNN_txtPassword').send_keys(ODD_M_PASS)
    driver.find_element_by_id('dnn_ctr433_Login_Login_DNN_cmdLogin').click()
    sleep(2)

    driver.get('https://www.oddsmonkey.com/Tools/Matchers/EachwayMatcher.aspx')
    sleep(2)

    driver.find_element_by_xpath(
        '//*[@id="dnn_ctr1157_View_RadGrid1_ctl00"]/thead/tr/th[17]/a').click(
        )
    sleep(2)

    driver.execute_script(
        '''window.open("https://www.sportingindex.com/fixed-odds","_blank");'''
    )
    sleep(2)

    driver.switch_to.window(driver.window_handles[1])
    WebDriverWait(driver, 30).until(
        EC.visibility_of_element_located(
            (By.ID, 'usernameCompact'))).send_keys(S_INDEX_USER)
    # driver.find_element_by_id('usernameCompact').send_keys(S_INDEX_USER)
    driver.find_element_by_id('passwordCompact').send_keys(S_INDEX_PASS)
    driver.find_element_by_id('submitLogin').click()
    sleep(0.5)
    print('Logged in')
    sys.stdout.flush()


print(f'Started at: {datetime.now().strftime("%H:%M:%S")}')
while True:
    try:
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (X11; CrOS x86_64 8172.45.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.64 Safari/537.36"
        )
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-setuid-sandbox")
        chrome_options.add_argument("--remote-debugging-port=9222") # this
        chrome_options.add_argument("--disable-dev-shm-using")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("start-maximized")
        # chrome_options.add_argument("disable-infobars")
        # chrome_options.add_argument("--headless")
        prefs = {"profile.default_content_setting_values.notifications": 2}
        chrome_options.add_experimental_option("prefs", prefs)
        driver = webdriver.Chrome(options=chrome_options)
        sys.stdout.flush()
        login(driver, ODD_M_USER, ODD_M_PASS, S_INDEX_USER, S_INDEX_PASS)
        scrape(driver, RETURNS_CSV, REFRESH_TIME, START_TIME)
    except KeyboardInterrupt:
        print('Exiting')
        sys.exit()
    # except (NoSuchElementException,
    #         TimeoutException,
    #         StaleElementReferenceException) as e:
    #     print('Element not found:', e)
    #     driver.quit()
    # except Exception as e:
    #     print('Unknown error ocurred:')
    #     print(e)
    finally:
        driver.quit()
