import sys
from time import sleep, time

from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from sporting_index import setup_sporting_index, sporting_index_bet, refresh_sporting_index, get_balance_sporting_index, output_race
from betfair_api import lay_ew, get_betfair_balance, output_lay_ew, login_betfair, get_race
from calculate_odds import calculate_stakes, calculate_profit
from write_to_csv import update_csv_sporting_index, update_csv_betfair

REFRESH_TIME = 62


def show_info(count, START_TIME):
    print(f'Time is: {datetime.now().strftime("%H:%M:%S")}', end='')
    diff = time() - START_TIME
    hours = int(diff // 60**2)
    mins = int(diff // 60 - hours * 60)
    secs = round(diff - (hours * 60 * 60) - (mins * 60))
    print(f"\tTime alive: {hours}:{mins}:{secs}")
    print(f'Refreshes: {count}')
    if datetime.now().hour >= 18:
        print('\nFinished matching today')
        print('-----------------------------------------------')
        sys.exit()


def find_races(driver):
    date_of_race = driver.find_element_by_xpath(
        '//table//tr[@id="dnn_ctr1157_View_RadGrid1_ctl00__0"]//td').text
    race_time = date_of_race[-5:].lower()
    date_of_race += ' %s' % datetime.today().year
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

    bookie_exchange = driver.find_element_by_xpath(
        '//*[@id="dnn_ctr1157_View_RadGrid1_ctl00__0"]/td[10]/a'
    ).get_attribute('href')

    rating = driver.find_element_by_xpath(
        '//*[@id="dnn_ctr1157_View_RadGrid1_ctl00__0"]/td[17]').text

    max_profit = driver.find_element_by_xpath(
        '//*[@id="dnn_ctr1157_View_RadGrid1_ctl00__0"]/td[20]').text.split(
            '£')[1]

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

    return {
        'date_of_race': date_of_race,
        'race_time': race_time,
        'horse_name': horse_name,
        'horse_odds': float(horse_odds),
        'race_venue': race_venue,
        'bookie_exchange': bookie_exchange,
        'rating': float(rating),
        'current_time': datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
        'lay_odds': float(lay_odds),
        'lay_odds_place': float(lay_odds_place),
        'place': float(place),
        'bookie_stake': float(bookie_stake),
        'win_stake': float(win_stake),
        'place_stake': float(place_stake),
        'max_profit': float(max_profit)
    }


def hide_race(driver, window=0):
    driver.switch_to.window(driver.window_handles[window])
    driver.find_element_by_xpath(
        '//table//tr[@id="dnn_ctr1157_View_RadGrid1_ctl00__0"]//td[55]//div//a'
    ).click()


def refresh_odds_monkey(driver):
    driver.switch_to.default_content()
    WebDriverWait(driver, 60).until(
        EC.element_to_be_clickable((
            By.XPATH,
            '//*[@id="dnn_ctr1157_View_RadToolBar1"]/div/div/div/ul/li[8]/div/button[1]'
        ))).click()
    # wait until spinner disappeared
    WebDriverWait(driver, 60).until(
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

    WebDriverWait(driver, 60).until(
        EC.visibility_of_element_located((
            By.XPATH,
            '//*[@id="dnn_ctr1157_View_RadToolBar1"]/div/div/div/ul/li[6]/a/span/span/span/span'
        ))).click()
    WebDriverWait(driver, 60).until(
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


def start_sporting_index(driver, race, bet, headers):
    driver.switch_to.window(driver.window_handles[0])
    refresh_odds_monkey(driver)
    if not driver.find_elements_by_class_name('rgNoRecords'):
        race.update(find_races(driver))
        print('Found no lay bet: %s' % race['horse_name'])
        race, bet_made = sporting_index_bet(driver, race)
        if bet_made:
            hide_race(driver)
            output_race(driver, race)
            update_csv_sporting_index(driver, race, headers)
            bet = True
    return bet


def start_betfair(driver, race, headers):
    driver.switch_to.window(driver.window_handles[2])
    refresh_odds_monkey(driver)
    if not driver.find_elements_by_class_name('rgNoRecords'):
        print('Found arbitrage bet:' % race['horse_name'])
        race.update(find_races(driver))
        if race['max_profit'] <= 0:
            return False
        betfair_balance = get_betfair_balance(headers)
        stakes_ok, bookie_stake, win_stake, place_stake, profit = calculate_stakes(
            race['balance'], betfair_balance, race['bookie_stake'],
            race['win_stake'], race['lay_odds'], race['place_stake'],
            race['lay_odds_place'], race['max_profit'])
        if not stakes_ok:
            return False
        minutes_until_race = (
            datetime.strptime(race['date_of_race'], '%d %b %H:%M %Y') -
            datetime.now()).total_seconds() / 60
        if minutes_until_race <= 1:
            print('Race too close to start time')
            return True

        market_ids, selection_id, got_race = get_race(race['date_of_race'],
                                                      race['race_venue'],
                                                      race['horse_name'])
        if not got_race:
            print("Race not found API")
            return True
        race['bookie_stake'] = bookie_stake
        race, bet_made = sporting_index_bet(driver, race, make_betfair_ew=True)
        if bet_made:
            lay_win, lay_place = lay_ew(market_ids, selection_id, win_stake,
                                        race['lay_odds'], place_stake,
                                        race['lay_odds_place'])
            betfair_balance = get_betfair_balance(headers)
            sporting_index_balance = get_balance_sporting_index(driver)
            win_profit, place_profit, lose_profit = calculate_profit(
                race['horse_odds'], bookie_stake, lay_win[4], lay_win[3],
                lay_place[4], lay_place[3], race['place'])
            min_profit = min(win_profit, place_profit, lose_profit)
            output_lay_ew(race, betfair_balance, sporting_index_balance,
                          min_profit, *lay_win, *lay_place, win_profit,
                          place_profit, lose_profit)
            update_csv_betfair(race, sporting_index_balance, bookie_stake,
                               win_stake, place_stake, betfair_balance,
                               lay_win[3], lay_place[3], min_profit,
                               lay_win[4], lay_place[4])
            return True
    return False


def scrape(driver, START_TIME):
    race = setup_sporting_index(driver)
    open_betfair_oddsmonkey(driver)
    count = 0
    driver.switch_to.window(driver.window_handles[0])
    while True:
        # So sporting index dosent logout
        if count % 2 == 0:
            refresh_sporting_index(driver)
            headers = login_betfair()
            if count % 10 == 0:
                show_info(count, START_TIME)

        bet = start_betfair(driver, race, headers)
        # bet = False  # remove when putting betfair in
        bet = start_sporting_index(driver, race, bet, headers)
        sys.stdout.flush()
        if not bet:
            sleep(REFRESH_TIME)  # betfair
        count += 1
