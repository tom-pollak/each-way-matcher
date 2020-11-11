import os
import sched
from time import sleep, time

from sim import find_stake
from dotenv import load_dotenv
from csv import DictWriter
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException

RETURNS_CSV = 'returns.csv'

REFRESH_TIME = 35
START_TIME = time()
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument(
    "user-agent=Mozilla/5.0 (X11; CrOS x86_64 8172.45.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.64 Safari/537.36"
)
prefs = {"profile.default_content_setting_values.notifications": 2}
chrome_options.add_experimental_option("prefs", prefs)
driver = webdriver.Chrome(options=chrome_options)

load_dotenv()
ODD_M_USER = os.environ.get('ODD_M_USER')
ODD_M_PASS = os.environ.get('ODD_M_PASS')
S_INDEX_USER = os.environ.get('S_INDEX_USER')
S_INDEX_PASS = os.environ.get('S_INDEX_PASS')

if None in [S_INDEX_USER, S_INDEX_PASS, ODD_M_USER, ODD_M_PASS]:
    raise NameError('Update .env with a vars')


def show_info(count, expected_returns):
    diff = time() - START_TIME
    hours = int(diff // 60**2)
    mins = int(diff // 60 - hours * 60)
    secs = round(diff - mins * 60)
    print(
        f'Time alive: {hours}:{mins}:{secs} - Expected returns: £{round(expected_returns, 2)}'
    )
    print(f'Refreshes: {count}')


def output_race():
    ew_stake = race['ew_stake']
    if not ew_stake:
        ew_stake = 'N/A'
    print(
        f"\nBet found: {race['horse_name']} - {race['horse_odds']} ({race['rating']}%) - probability: {race['returns_probability']}"
    )
    print(f"\t{race['date_of_race']} - {race['race_venue']}")
    print(f"\tCurrent balance: {race['balance']}, stake: {race['ew_stake']}")


def login():
    driver.get('https://www.oddsmonkey.com/oddsmonkeyLogin.aspx?returnurl=%2f')
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


def change_to_decimal():
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
    balance = WebDriverWait(driver, 20).until(
        EC.visibility_of_element_located((By.CLASS_NAME, 'btn-balance'))).text
    balance = balance.replace(' ', '')
    balance = balance.replace('£', '')
    balance = balance.replace('▸', '')
    return float(balance)


def update_csv(race):
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

    rating = driver.find_element_by_xpath(
        '//*[@id="dnn_ctr1157_View_RadGrid1_ctl00__0"]/td[17]').text

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
        'current_time': datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    }


def make_sporting_index_bet(race, expected_returns):
    driver.switch_to.window(driver.window_handles[1])
    driver.refresh()
    el = WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable((By.LINK_TEXT, race['race_time'])))
    el.click()
    # Check if the horse on the page
    # Can happen if we choose event with same time but wrong location

    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CLASS_NAME, 'horseName')))
    if race['horse_name'] not in driver.page_source:
        print('No horse found\n')
    else:
        horse_name_xpath = f"//td[contains(text(), '{race['horse_name']}')]/following-sibling::td[5]/wgt-price-button/button"
        driver.find_element_by_xpath(horse_name_xpath).click()

        cur_odd_price = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located(
                (By.TAG_NAME, 'wgt-live-price-raw')))
        if cur_odd_price != '':
            race['balance'] = get_balance_sporting_index(driver)
            race['ew_stake'], race['returns_probability'] = find_stake(race['horse_odds'],
                                          race['rating'],
                                          race['balance'])
            output_race()
            if float(cur_odd_price.text) == float(race['horse_odds']):
                if race['ew_stake']:
                    driver.find_element_by_class_name('ng-pristine').send_keys(
                        str(race['ew_stake']))
                    driver.find_element_by_xpath(
                        '// input[ @ type = "checkbox"]').click()
                    driver.find_element_by_class_name('placeBetBtn').click()
                    el = WebDriverWait(driver, 30).until(
                        EC.element_to_be_clickable(
                            (By.XPATH,
                             "//button[contains(text(), 'Continue')]")))
                    el.click()
                    print('Bet made\n')
                    expected_returns += race['ew_stake'] * race['rating'] / 100, 2
                    driver.refresh()
                    update_csv(race)
                else:
                    print('Stake must be too small to make reliable profit')
                    driver.find_element_by_xpath(
                        "//li[@class='close']//wgt-spin-icon[@class='close-bet']"
                    ).click()
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


login()
change_to_decimal()
count = 0
expected_returns = 0
race = {'rating': 100, 'returns_probability': 95, 'ew_stake': 0.1}
race['balance'] = get_balance_sporting_index(driver)
driver.switch_to.window(driver.window_handles[0])
while True:
    # So sporting index dosent logout
    if count % 4 == 0:
        refresh_sporting_index(driver, count)
        show_info(count, expected_returns)

    driver.switch_to.window(driver.window_handles[0])
    sleep(REFRESH_TIME)
    refresh_odds_monkey(driver)
    if not driver.find_elements_by_class_name('rgNoRecords'):
        race.update(find_races())
        if float(race['horse_odds']) != 100:
            try:
                race, expected_returns = make_sporting_index_bet(race, expected_returns)
            except NoSuchElementException as e:
                print('Bet failed\n%s\n' % e)
                print('------------------------------\n')
    count += 1
