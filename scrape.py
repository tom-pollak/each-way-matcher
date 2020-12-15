# -*- coding: utf-8 -*-
import os
import sys
import sched
from time import sleep, time

from sim import find_stake
from calculate_odds import kelly_criterion
from dotenv import load_dotenv
from csv import DictWriter
from datetime import datetime
# from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException

# RETURNS_CSV = 'returns.csv'
#
# REFRESH_TIME = 35
# START_TIME = time()
# # chrome_options = webdriver.ChromeOptions()
# # chrome_options.add_argument(
# #     "user-agent=Mozilla/5.0 (X11; CrOS x86_64 8172.45.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.64 Safari/537.36"
# # )
# # prefs = {"profile.default_content_setting_values.notifications": 2}
# # chrome_options.add_experimental_option("prefs", prefs)
# # driver = webdriver.Chrome(options=chrome_options)
#
# ODD_M_USER = os.environ.get('ODD_M_USER')
# ODD_M_PASS = os.environ.get('ODD_M_PASS')
# S_INDEX_USER = os.environ.get('S_INDEX_USER')
# S_INDEX_PASS = os.environ.get('S_INDEX_PASS')

# if None in [S_INDEX_USER, S_INDEX_PASS, ODD_M_USER, ODD_M_PASS]:
#     raise NameError('Update .env with a vars')


def show_info(driver, count, expected_returns, START_TIME):
    if datetime.now().hour >= 18:
        sys.exit()
    diff = time() - START_TIME
    hours = int(diff // 60**2)
    mins = int(diff // 60 - hours * 60)
    secs = round(diff - mins * 60)
    print(
        f"Time alive: {hours}:{mins}:{secs} - Expected returns: £{round(expected_returns, 2)}"
    )
    print(f'Refreshes: {count}')


def output_race(race):
    ew_stake = race['ew_stake']
    if not ew_stake:
        ew_stake = 'N/A'
    print(
        f"Bet found: {race['horse_name']} - {race['horse_odds']} ({race['rating']}%) - probability: {race['returns_probability']}"
    )
    print(f"\t{race['date_of_race']} - {race['race_venue']}")
    print(f"\tCurrent balance: {race['balance']}, stake: {race['ew_stake']}")


def login(driver, ODD_M_USER, ODD_M_PASS, S_INDEX_USER, S_INDEX_PASS):
    driver.get('https://www.oddsmonkey.com/oddsmonkeyLogin.aspx?returnurl=%2f')
    print('Got page')
    # print(driver.page_source)
    WebDriverWait(driver, 30).until(
        EC.visibility_of_element_located(
            (By.ID,
             'dnn_ctr433_Login_Login_DNN_txtUsername'))).send_keys(ODD_M_USER)
    # driver.find_element_by_id(
    #     'dnn_ctr433_Login_Login_DNN_txtUsername').send_keys(ODD_M_USER)
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


def change_to_decimal(driver):
    driver.get(
        'https://www.sportingindex.com/fixed-odds/horse-racing/race-calendar')
    WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable(
            (By.XPATH, '//a[@class="btn-my-account"]'))).click()
    # driver.find_element_by_xpath('//a[@class="btn-my-account"]').click()
    sleep(0.5)
    driver.find_element_by_id('decimalBtn').click()
    sleep(0.5)
    driver.refresh()
    sleep(2)
    driver.switch_to.window(driver.window_handles[0])
    sleep(0.5)


def get_balance_sporting_index(driver):
    driver.switch_to.window(driver.window_handles[1])
    balance = WebDriverWait(driver, 40).until(
        EC.visibility_of_element_located((By.CLASS_NAME, 'btn-balance'))).text
    balance = balance.replace(' ', '')
    balance = balance.replace('£', '')
    balance = balance.replace('▸', '')
    return float(balance)


def update_csv(race, RETURNS_CSV):
    csv_columns = [
        'date_of_race',
        'horse_name',
        'horse_odds',
        'race_venue',
        'ew_stake',
        'balance',
        'rating',
        'current_time',
        'returns_probability'
    ]
    with open(RETURNS_CSV, 'a+', newline='') as returns_csv:
        csv_writer = DictWriter(returns_csv,
                                fieldnames=csv_columns,
                                extrasaction='ignore')
        csv_writer.writerow(race)


def find_races(driver):
    date_of_race = driver.find_element_by_xpath(
        '//table//tr[@id="dnn_ctr1157_View_RadGrid1_ctl00__0"]//td'
    ).text.lower()
    race_time = date_of_race[-5:]
    race_venue = driver.find_element_by_xpath(
        '//table//tr[@id="dnn_ctr1157_View_RadGrid1_ctl00__0"]//td[8]'
    ).text.lower().strip()
    sizestring = len(race_venue)
    race_venue = race_venue[:sizestring - 5].strip().title()

    horse_name = driver.find_element_by_xpath(
        '//table//tr[@id="dnn_ctr1157_View_RadGrid1_ctl00__0"]//td[9]'
    ).text.title()

    horse_odds = driver.find_element_by_xpath(
        '//table//tr[@id="dnn_ctr1157_View_RadGrid1_ctl00__0"]//td[13]').text

    win_exchange = driver.find_element_by_xpath(
        '//table//tr[@id="dnn_ctr1157_View_RadGrid1_ctl00__0"]//td[14]//a'
    ).get_attribute('href')

    rating = driver.find_element_by_xpath(
        '//*[@id="dnn_ctr1157_View_RadGrid1_ctl00__0"]/td[17]').text

    driver.find_element_by_xpath(
        '//*[@id="dnn_ctr1157_View_RadGrid1_ctl00_ctl04_calcButton"]').click()

    # sleep(5)
    # lay_odds = driver.find_element_by_xpath(
    #     '/html/body/form/div[5]/div[3]/div/div/div[2]/div/div[2]/div/div[2]/div/input'
    # ).get_attribute('value')
    # lay_odds = driver.find_element_by_xpath(
    #     '//*[@id="txtLayOdds_win"]').get_attribute('value')
    driver.switch_to.frame('RadWindow2')
    lay_odds = WebDriverWait(driver, 60).until(
        EC.presence_of_element_located(
            (By.ID, 'txtLayOdds_win'))).get_attribute('value')

    lay_odds_place = driver.find_element_by_xpath(
        '//*[@id="txtLayOdds_place"]').get_attribute('value')

    place = driver.find_element_by_xpath(
        '//*[@id="txtPlacePayout"]').get_attribute('value')

    driver.switch_to.default_content()
    driver.find_element_by_class_name('rwCloseButton').click()
    driver.find_element_by_xpath(
        '//table//tr[@id="dnn_ctr1157_View_RadGrid1_ctl00__0"]//td[55]//div//a'
    ).click()

    return {
        'date_of_race': date_of_race,
        'race_time': race_time,
        'horse_name': horse_name,
        'horse_odds': float(horse_odds),
        'race_venue': race_venue,
        'win_exchange': win_exchange,
        'rating': float(rating),
        'current_time': datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
        'lay_odds': float(lay_odds),
        'lay_odds_place': float(lay_odds_place),
        'place': float(place)
    }


def make_sporting_index_bet(driver, race, expected_returns, RETURNS_CSV):
    driver.find_element_by_class_name('ng-pristine').send_keys(
        str(race['ew_stake']))
    driver.find_element_by_xpath('// input[ @ type = "checkbox"]').click()
    try:
        driver.find_element_by_class_name('placeBetBtn').click()
    except NoSuchElementException:
        print('Odds have changed')
        driver.find_element_by_xpath(
            "//li[@class='close']//wgt-spin-icon[@class='close-bet']").click()

    el = WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(text(), 'Continue')]")))
    el.click()
    print('Bet made\n')
    expected_returns += race['ew_stake'] * (race['rating'] / 100 - 1)
    driver.refresh()
    update_csv(race, RETURNS_CSV)
    print('Stake must be too small to make reliable profit')
    driver.find_element_by_xpath(
        "//li[@class='close']//wgt-spin-icon[@class='close-bet']").click()
    return expected_returns


def get_sporting_index_page(driver, race):
    driver.switch_to.window(driver.window_handles[1])
    driver.refresh()
    WebDriverWait(driver, 60).until(
        EC.presence_of_element_located((
            By.XPATH,
            f"//th[contains(text(), '{race['race_venue']}')]/../../../tbody/tr/td/span/a/strong[contains(text(), '{race['race_time']}')]/.."
        ))).click()


def sporting_index_bet(driver, race, expected_returns, RETURNS_CSV):
    get_sporting_index_page(driver, race)
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CLASS_NAME, 'horseName')))
    horse_name_xpath = f"//td[contains(text(), '{race['horse_name']}')]/following-sibling::td[5]/wgt-price-button/button"
    driver.find_element_by_xpath(horse_name_xpath).click()

    cur_odd_price = WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.TAG_NAME, 'wgt-live-price-raw')))
    if cur_odd_price != '':
        race['balance'] = get_balance_sporting_index(driver)
        race['ew_stake'], race['expected_returns'] = kelly_criterion(race['horse_odds'], race['lay_odds'], race['lay_odds_place'], race['place'], race['balance'])
        if race['ew_stake'] < 0.1:
            print(f"Odds are too small to bet - {race['ew_stake']}")
            return race, 0
        output_race(race)
        if float(cur_odd_price.text) == float(race['horse_odds']):
            expected_returns = make_sporting_index_bet(driver,
                                                       race,
                                                       expected_returns,
                                                       RETURNS_CSV)
        else:
            print(
                f"Odds have changed - before: {float(race['horse_odds'])} after: {float(cur_odd_price.text)}\n"
            )
            driver.find_element_by_xpath(
                "//li[@class='close']//wgt-spin-icon[@class='close-bet']"
            ).click()
    else:
        print('cur_odd_price is an empty string')
    driver.get(
        'https://www.sportingindex.com/fixed-odds/horse-racing/race-calendar')
    return race, expected_returns


def refresh_sporting_index(driver, count):
    driver.switch_to.window(driver.window_handles[1])
    sleep(0.1)
    driver.refresh()


def refresh_odds_monkey(driver):
    driver.find_element_by_id(
        'dnn_ctr1157_View_RadToolBar1_i11_lblRefreshText').click()
    # wait till spinner disappeared
    WebDriverWait(driver, 30).until(
        EC.invisibility_of_element_located((
            By.ID,
            'dnn_ctr1157_View_RadAjaxLoadingPanel1dnn_ctr1157_View_RadGrid1')))


def main(driver,
         RETURNS_CSV,
         REFRESH_TIME,
         START_TIME,
         ODD_M_USER,
         ODD_M_PASS,
         S_INDEX_USER,
         S_INDEX_PASS):
    load_dotenv()
    login(driver, ODD_M_USER, ODD_M_PASS, S_INDEX_USER, S_INDEX_PASS)
    change_to_decimal(driver)
    count = 0
    expected_returns = 0
    bet = True
    race = {'rating': 100, 'returns_probability': 95, 'ew_stake': 0.1}
    race['balance'] = get_balance_sporting_index(driver)
    driver.switch_to.window(driver.window_handles[0])
    while True:
        # So sporting index dosent logout
        if count % 4 == 0:
            refresh_sporting_index(driver, count)
            show_info(driver, count, expected_returns, START_TIME)

        driver.switch_to.window(driver.window_handles[0])
        if not bet:
            sleep(REFRESH_TIME)
        bet = False
        refresh_odds_monkey(driver)
        if not driver.find_elements_by_class_name('rgNoRecords'):
            race.update(find_races(driver))
            if float(race['horse_odds']) != 100:
                bet = True
                race, expected_returns = sporting_index_bet(driver, race, expected_returns, RETURNS_CSV)
        count += 1
