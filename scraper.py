import os
import sched
from time import sleep

from dotenv import load_dotenv
from csv import DictWriter
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException

# EW_STAKE = 1 # NB the bet will be double this amount as it bets "each way"
REFRESH_TIME = 15 # No of seconds before refreshing oddsmonkey
RESULTS_CSV = 'results.csv'
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
    driver.switch_to.window(driver.window_handles[1])
    # second_page = "https://www.sportingindex.com/fixed-odds"

    # driver.get(second_page);
    sleep(1)
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


def get_balance_sporting_index(driver):
    driver.switch_to.window(driver.window_handles[1])
    balance = WebDriverWait(driver, 20).until(
        EC.visibility_of_element_located((By.CLASS_NAME, 'btn-balance'))).text
    balance = balance.replace(' ', '')
    balance = balance.replace('£', '')
    balance = balance.replace('▸', '')
    ew_stake = float(balance) / 100
    ew_stake = float("{:.2f}".format(float(ew_stake)))
    if ew_stake < 0.1:
        ew_stake = 0.10
    return balance, ew_stake


def update_csv(race):
    csv_columns = [
        'date_of_race',
        'horse_name',
        'horse_odds',
        'race_venue',
        'ew_stake',
        'balance'
    ]
    with open(RESULTS_CSV, 'a+', newline='') as results_csv:
        csv_writer = DictWriter(results_csv,
                                fieldnames=csv_columns,
                                extrasaction='ignore')
        csv_writer.writerow(race)


def find_races(balance, ew_stake):
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

    print(f'\nBet found: {horse_name} - {horse_odds} ', end='')
    print(f'at {race_venue} {date_of_race}')
    print(f'Current balance {balance}, stake: {ew_stake}')
    return {
        'date_of_race': date_of_race,
        'race_time': race_time,
        'horse_name': horse_name,
        'horse_odds': horse_odds,
        'race_venue': race_venue,
        'ew_stake': ew_stake,
        'balance': balance,
        'win_exchange': win_exchange,
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
        print('No horse found\n')
    else:
        horse_name_xpath = f"//td[contains(text(), '{race['horse_name']}')]/following-sibling::td[5]/wgt-price-button/button"
        driver.find_element_by_xpath(horse_name_xpath).click()

        cur_odd_price = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located(
                (By.TAG_NAME, 'wgt-live-price-raw')))
        if cur_odd_price != '':
            if float(cur_odd_price.text) == float(race['horse_odds']):
                driver.find_element_by_class_name('ng-pristine').send_keys(
                    str(race['ew_stake']))
                driver.find_element_by_xpath(
                    '// input[ @ type = "checkbox"]').click()
                driver.find_element_by_class_name('placeBetBtn').click()
                el = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, "//button[contains(text(), 'Continue')]")))
                el.click()
                print('Bet made\n')
                driver.refresh()
                race['balance'], race['ew_stake'] = get_balance_sporting_index(driver)
                update_csv(race)
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
    return get_balance_sporting_index(driver)


def refresh_sporting_index(driver, count):
    print(f'Refreshes: {count}')
    driver.switch_to.window(driver.window_handles[1])
    sleep(0.1)
    driver.refresh()


def refresh_odds_monkey(driver):
    driver.find_element_by_id(
        'dnn_ctr1157_View_RadToolBar1_i11_lblRefreshText').click()
    # wait till spinner disappeared
    WebDriverWait(driver, 10).until(
        EC.invisibility_of_element_located((
            By.ID,
            'dnn_ctr1157_View_RadAjaxLoadingPanel1dnn_ctr1157_View_RadGrid1')))


login()
change_to_decimal()
# URL = driver.current_url
count = 0
balance, ew_stake = get_balance_sporting_index(driver)
driver.switch_to.window(driver.window_handles[0])
while True:
    # So sporting index dosent logout
    if count % 25 == 0:
        refresh_sporting_index(driver, count)

    # if URL == driver.current_url:
    driver.switch_to.window(driver.window_handles[0])
    sleep(REFRESH_TIME)
    refresh_odds_monkey(driver)
    if not driver.find_elements_by_class_name('rgNoRecords'):
        race = find_races(balance, ew_stake)
        try:
            make_sporting_index_bet(race)
        except NoSuchElementException as e:
            print('\nBet failed\n%s\n' % e)
            print('------------------------------\n')
    count += 1
