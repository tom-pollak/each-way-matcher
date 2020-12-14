import os
import sys
from time import time
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from scrape import main

RETURNS_CSV = 'returns.csv'
REFRESH_TIME = 35
START_TIME = time()
ODD_M_USER = os.environ.get('ODD_M_USER')
ODD_M_PASS = os.environ.get('ODD_M_PASS')
S_INDEX_USER = os.environ.get('S_INDEX_USER')
S_INDEX_PASS = os.environ.get('S_INDEX_PASS')
while True:
    try:
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
        # chrome_options.add_argument("disable-infobars") 
        # chrome_options.add_argument("--headless")
        prefs = {"profile.default_content_setting_values.notifications": 2}
        chrome_options.add_experimental_option("prefs", prefs)
        driver = webdriver.Chrome(options=chrome_options)
        main(driver,
             RETURNS_CSV,
             REFRESH_TIME,
             START_TIME,
             ODD_M_USER,
             ODD_M_PASS,
             S_INDEX_USER,
             S_INDEX_PASS)
    except KeyboardInterrupt:
        print('Exiting')
        sys.exit()
    except (NoSuchElementException, TimeoutException) as e:
        print('Element not found:', e)
        driver.quit()
    except Exception as e:
        print('Unknown error ocurred:')
        print(e)
    finally:
        driver.quit()
