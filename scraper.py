import os
import sched
import time
from time import sleep

from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException

REFRESH_TIME = 5
chrome_options = webdriver.ChromeOptions()
prefs = {"profile.default_content_setting_values.notifications": 2}
chrome_options.add_experimental_option("prefs", prefs)
driver = webdriver.Chrome(options=chrome_options)

load_dotenv()
S_INDEX_USER = os.environ.get('S_INDEX_USER')
S_INDEX_PASS = os.environ.get('S_INDEX_PASS')
ODD_M_USER = os.environ.get('ODD_M_USER')
ODD_M_PASS = os.environ.get('ODD_M_PASS')

if None in [S_INDEX_USER, S_INDEX_PASS, ODD_M_USER, ODD_M_PASS]:
    raise NameError('Update .env with a vars')


def login():
    driver.get('https://www.oddsmonkey.com/oddsmonkeyLogin.aspx?returnurl=%2f')
    sleep(2)
    driver.find_element_by_id(
        'dnn_ctr433_Login_Login_DNN_txtUsername').send_keys(ODD_M_USER)
    driver.find_element_by_id(
        'dnn_ctr433_Login_Login_DNN_txtPassword').send_keys(ODD_M_PASS)
    driver.find_element_by_id('dnn_ctr433_Login_Login_DNN_cmdLogin').click()
    sleep(2)
    driver.get('https://www.oddsmonkey.com/Tools/Matchers/EachwayMatcher.aspx')

    sleep(2)
    driver.execute_script(
        '''window.open("https://www.sportingindex.com/fixed-odds","_blank");'''
    )
    sleep(2)
    driver.switch_to.window(driver.window_handles[-1])
    # second_page = "https://www.sportingindex.com/fixed-odds"

    # driver.get(second_page);
    sleep(0.5)
    driver.find_element_by_id('usernameCompact').send_keys(S_INDEX_USER)
    driver.find_element_by_id('passwordCompact').send_keys(S_INDEX_PASS)
    driver.find_element_by_id('submitLogin').click()
    sleep(0.5)


def change_to_decimal():
    driver.get(
        'https://www.sportingindex.com/fixed-odds/horse-racing/race-calendar')
    sleep(2)
    driver.find_element_by_xpath('//a[@class="btn-my-account"]').click()
    sleep(0.5)
    driver.find_element_by_id('decimalBtn').click()
    sleep(0.5)
    driver.refresh()
    sleep(2)
    driver.switch_to.window(driver.window_handles[0])
    sleep(0.5)


def find_races():
    date_of_race = driver.find_element_by_xpath(
        '//table//tr[@id="dnn_ctr1157_View_RadGrid1_ctl00__0"]//td'
    ).text.lower()
    race_time = date_of_race[-5:]
    race_venue = driver.find_element_by_xpath(
        '//table//tr[@id="dnn_ctr1157_View_RadGrid1_ctl00__0"]//td[8]'
    ).text.lower().strip()
    sizestring = len(race_venue)
    race_venue = race_venue[:sizestring - 5].strip()

    horse_name = driver.find_element_by_xpath(
        '//table//tr[@id="dnn_ctr1157_View_RadGrid1_ctl00__0"]//td[9]'
    ).text.title()

    horse_odds = driver.find_element_by_xpath(
        '//table//tr[@id="dnn_ctr1157_View_RadGrid1_ctl00__0"]//td[13]').text

    win_exchange = driver.find_element_by_xpath(
        '//table//tr[@id="dnn_ctr1157_View_RadGrid1_ctl00__0"]//td[14]//a'
    ).get_attribute('href')

    driver.find_element_by_xpath(
        '//table//tr[@id="dnn_ctr1157_View_RadGrid1_ctl00__0"]//td[55]//div//a'
    ).click()
    # driver.find_element_by_id("submitLogin").click()

    print(f'Bet found: {horse_name} - {horse_odds} ', end='')
    print(f'at {race_venue} {date_of_race} {race_time}\n')
    return {
        'date_of_race': date_of_race,
        'race_time': race_time,
        'race_venue': race_venue,
        'horse_name': horse_name,
        'horse_odds': horse_odds,
        'win_exchange': win_exchange
    }


def make_sporting_index_bet(race):
    driver.switch_to.window(driver.window_handles[1])
    driver.refresh()
    el = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.LINK_TEXT, race['race_time'])))
    el.click()
    # Check if the horse on the page
    # Can happen if we choose event with same time but wrong location

    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CLASS_NAME, 'horseName')))
    if race['horse_name'] not in driver.page_source:
        print('No horse found')
    else:
        horse_name_xpath = f"//td[contains(text(), '{race['horse_name']}')]/following-sibling::td[5]/wgt-price-button/button"
        driver.find_element_by_xpath(horse_name_xpath).click()

        cur_odd_price = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located(
                (By.TAG_NAME, 'wgt-live-price-raw')))
        if float(cur_odd_price.text) != float(race['horse_odds']):
            print(
                f"Odds have changed - before: {float(race['horse_odds'])} after: {float(cur_odd_price.text)}"
            )
        driver.find_element_by_class_name('ng-pristine').send_keys('2')
        driver.find_element_by_xpath('// input[ @ type = "checkbox"]').click()
        driver.find_element_by_class_name('placeBetBtn').click()
        el = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(text(), 'Continue')]")))
        el.click()
        print('Bet made')
        sleep(3)
    driver.get(
        'https://www.sportingindex.com/fixed-odds/horse-racing/race-calendar')
    sleep(3)


login()
change_to_decimal()
# URL = driver.current_url
count = 0
while True:
    count += 1
    # if URL == driver.current_url:
    driver.switch_to.window(driver.window_handles[0])
    sleep(REFRESH_TIME)

    driver.find_element_by_id(
        'dnn_ctr1157_View_RadToolBar1_i11_lblRefreshText').click()
    sleep(3)
    if not driver.find_elements_by_class_name('rgNoRecords'):
        race = find_races()
        try:
            make_sporting_index_bet(race)
        except NoSuchElementException as e:
            print('Bet failed\n%s\n' % e)
            print('------------------------------')

    # else:
    #     print('No bets found')
    # So sporting index dosent logout
    if count % 25 == 0:
        print(f'Refreshes: {count}')
        driver.switch_to.window(driver.window_handles[1])
        sleep(0.2)
        driver.refresh()
        sleep(3)
