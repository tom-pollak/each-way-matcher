# -*- coding: utf-8 -*-
import sys
from time import sleep, time

from csv import DictWriter
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from sporting_index import setup_sporting_index, sporting_index_bet, refresh_sporting_index
from betfair_api import lay_ew, calculate_stakes, get_betfair_balance, output_lay_ew, login_betfair


def show_info(driver, count, START_TIME):
    print(f'Time is: {datetime.now().strftime("%H:%M:%S")}', end='')
    diff = time() - START_TIME
    hours = int(diff // 60**2)
    mins = int(diff // 60 - hours * 60)
    secs = round(diff - hours * 60 - mins * 60)
    print(f"\tTime alive: {hours}:{mins}:{secs}")
    print(f'Refreshes: {count}')
    if datetime.now().hour >= 19:
        print('Finished matching today')
        sys.exit()


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
        'expected_value',
        'expected_return'
    ]
    with open(RETURNS_CSV, 'a+', newline='') as returns_csv:
        csv_writer = DictWriter(returns_csv,
                                fieldnames=csv_columns,
                                extrasaction='ignore')
        csv_writer.writerow(race)


def find_races(driver, hide=True):
    date_of_race = driver.find_element_by_xpath(
        '//table//tr[@id="dnn_ctr1157_View_RadGrid1_ctl00__0"]//td').text
    race_time = date_of_race[-5:].lower()
    date_of_race += ' %s' % datetime.today().year
    # date_of_race = datetime.strptime(date_of_race, '%d %b %H:%M %Y')
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

    driver.switch_to.frame('RadWindow2')
    lay_odds = WebDriverWait(driver, 60).until(
        EC.presence_of_element_located(
            (By.ID, 'txtLayOdds_win'))).get_attribute('value')

    lay_odds_place = driver.find_element_by_xpath(
        '//*[@id="txtLayOdds_place"]').get_attribute('value')

    place = driver.find_element_by_xpath(
        '//*[@id="txtPlacePayout"]').get_attribute('value')

    bookie_stake = driver.find_element_by_xpath(
        '//*[@id="lblStep1"]/strong[1]').text.replace('£', '')
    win_stake = driver.find_element_by_xpath(
        '//*[@id="lblStep2"]/strong[1]').text.replace('£', '')
    place_stake = driver.find_element_by_xpath(
        '//*[@id="lblStep3"]/b').text.replace('£', '')

    driver.switch_to.default_content()
    driver.find_element_by_class_name('rwCloseButton').click()
    if hide:
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
        'place': float(place),
        'bookie_stake': float(bookie_stake),
        'win_stake': float(win_stake),
        'place_stake': float(place_stake),
    }


def refresh_odds_monkey(driver):
    WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable(
            (By.ID,
             'dnn_ctr1157_View_RadToolBar1_i11_lblRefreshText'))).click()
    # wait till spinner disappeared
    WebDriverWait(driver, 30).until(
        EC.invisibility_of_element_located((
            By.ID,
            'dnn_ctr1157_View_RadAjaxLoadingPanel1dnn_ctr1157_View_RadGrid1')))


def open_betfair_oddsmonkey(driver):
    driver.execute_script(
        '''window.open("https://www.oddsmonkey.com/Tools/Matchers/EachwayMatcher.aspx","_blank");'''
    )
    driver.switch_to.window(driver.window_handles[2])

    # WebDriverWait(driver, 30).until(
    #     EC.element_to_be_clickable(
    #         (By.ID,
    #          'dnn_ctr1157_View_RadToolBar1_i11_lblRefreshText'))).click()

    WebDriverWait(driver, 30).until(
        EC.visibility_of_element_located((
            By.XPATH,
            '//*[@id="dnn_ctr1157_View_RadToolBar1"]/div/div/div/ul/li[6]/a/span/span/span/span'
        ))).click()
    WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable(
            (By.XPATH, '//*[@id="headingFour"]/h4/a'))).click()
    sleep(0.5)
    driver.find_element_by_xpath(
        '//*[@id="dnn_ctr1157_View_rlbExchanges"]/div/div/label/input').click(
        )
    driver.find_element_by_xpath(
        '//*[@id="dnn_ctr1157_View_rlbExchanges_i0"]/label/input').click()
    driver.find_element_by_xpath(
        '//*[@id="dnn_ctr1157_View_btnApplyFilter"]').click()
    driver.find_element_by_xpath(
        '//*[@id="dnn_ctr1157_ModuleContent"]/div[10]/div[1]/a').click()
    sleep(0.5)


def start_sporting_index(driver, race, RETURNS_CSV, bet):
    driver.switch_to.window(driver.window_handles[0])
    refresh_odds_monkey(driver)
    if not driver.find_elements_by_class_name('rgNoRecords'):
        race.update(find_races(driver))
        bet = True
        race, bet_made = sporting_index_bet(driver, race)
        if bet_made:
            update_csv(race, RETURNS_CSV)
    return bet


def start_betfair(driver, race):
    bet = False
    driver.switch_to.window(driver.window_handles[2])
    refresh_odds_monkey(driver)
    if not driver.find_elements_by_class_name('rgNoRecords'):
        race.update(find_races(driver, hide=False))
        bet = True
        betfair_balance = get_betfair_balance()
        stakes_ok, bookie_stake, win_stake, place_stake = calculate_stakes(race['balance'],
                                                                           betfair_balance,
                                                                           race['bookie_stake'],
                                                                           race['horse_odds'],
                                                                           race['win_stake'],
                                                                           race['lay_odds'],
                                                                           race['place_stake'],
                                                                           race['lay_odds_place'])
        if not stakes_ok:
            return True
        race['bookie_stake'] = bookie_stake
        race, bet_made = sporting_index_bet(driver, race, make_betfair_ew=True)
        if bet_made:
            bet_made = lay_ew(race['race_time'],
                              race['race_venue'],
                              race['horse_name'],
                              race['lay_odds'],
                              win_stake,
                              race['lay_odds_place'],
                              place_stake)
        if bet_made:
            betfair_balance = get_betfair_balance()
            output_lay_ew(race, betfair_balance)
    return bet


def scrape(driver, RETURNS_CSV, REFRESH_TIME, START_TIME):
    race = setup_sporting_index(driver)
    # uncomment these for betfair api
    # open_betfair_oddsmonkey(driver)
    # login_betfair()
    count = 0
    driver.switch_to.window(driver.window_handles[0])
    while True:
        # So sporting index dosent logout
        if count % 4 == 0:
            refresh_sporting_index(driver, count)
            show_info(driver, count, START_TIME)

        # bet = start_betfair(driver, race) # betfair
        bet = False # remove when putting betfair in
        bet = start_sporting_index(driver, race, RETURNS_CSV, bet)
        sys.stdout.flush()
        if not bet:
            sleep(REFRESH_TIME)
        count += 1
