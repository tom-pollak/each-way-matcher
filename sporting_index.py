from time import sleep
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException, NoSuchElementException

from calculate_odds import kelly_criterion


def change_to_decimal(driver):
    WebDriverWait(driver, 60).until(
        EC.element_to_be_clickable(
            (By.XPATH, '//a[@class="btn-my-account"]'))).click()
    WebDriverWait(driver,
                  60).until(EC.element_to_be_clickable(
                      (By.ID, 'decimalBtn'))).click()


def output_race(race, bet_made=True):
    print(f"Bet found: {race['horse_name']} - {race['horse_odds']}")
    print(f"\tLay win: {race['lay_odds']} Lay place: {race['lay_odds_place']}")
    print(
        f"\tExpected value: {race['expected_value']}, Expected return: {race['expected_return']}"
    )
    print(f"\t{race['date_of_race']} - {race['race_venue']}")
    print(f"\tCurrent balance: {race['balance']}, stake: {race['ew_stake']}")
    if bet_made:
        print('Bet made\n')


def get_balance_sporting_index(driver, retry=False):
    driver.switch_to.window(driver.window_handles[1])
    try:
        balance = WebDriverWait(driver, 60).until(
            EC.visibility_of_element_located(
                (By.CLASS_NAME, 'btn-balance'))).text
        count = 0
        while balance == 'BALANCE' and count < 10:
            sleep(0.5)
            balance = driver.find_element_by_class_name('btn-balance').text
            count += 1
        if balance == 'BALANCE' and not retry:
            raise Exception
    except:
        if not retry:
            driver.refresh()
            get_balance_sporting_index(driver, retry=True)
        raise Exception("Couldn't find balance")

    balance = balance.replace(' ', '')
    balance = balance.replace('£', '')
    balance = balance.replace('▸', '')
    return float(balance)


def refresh_sporting_index(driver, count):
    driver.switch_to.window(driver.window_handles[1])
    sleep(0.1)
    driver.refresh()


def make_sporting_index_bet(driver, race):
    for i in range(3):
        try:
            WebDriverWait(driver, 60).until(
                EC.visibility_of_element_located(
                    (By.CLASS_NAME,
                     'ng-pristine'))).send_keys(str(race['ew_stake']))
            break
        except StaleElementReferenceException:
            driver.refresh()
    else:
        return False

    driver.find_element_by_xpath('// input[ @ type = "checkbox"]').click()
    try:
        driver.find_element_by_class_name('placeBetBtn').click()
    except NoSuchElementException:
        driver.find_element_by_xpath(
            "//li[@class='close']//wgt-spin-icon[@class='close-bet']").click()
        return False

    WebDriverWait(driver, 60).until(
        EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(text(), 'Continue')]"))).click()
    return True


def get_sporting_index_page(driver, race):
    driver.switch_to.window(driver.window_handles[1])
    driver.get(
        'https://www.sportingindex.com/fixed-odds/horse-racing/race-calendar')
    WebDriverWait(driver, 60).until(
        EC.presence_of_element_located((
            By.XPATH,
            f"//th[contains(text(), '{race['race_venue']}')]/../../../tbody/tr/td/span/a/strong[contains(text(), '{race['race_time']}')]/.."
        ))).click()


def sporting_index_bet(driver, race, retry=False, make_betfair_ew=False):
    get_sporting_index_page(driver, race)
    horse_name_xpath = f"//td[contains(text(), '{race['horse_name']}')]/following-sibling::td[5]/wgt-price-button/button"
    try:
        for i in range(3):
            try:
                horse_button = WebDriverWait(driver, 60).until(
                    EC.presence_of_element_located(
                        (By.XPATH, horse_name_xpath)))
                cur_odd_price = horse_button.text
                horse_button.click()
                break
            except StaleElementReferenceException:
                driver.refresh()
        else:
            raise NoSuchElementException

    except (NoSuchElementException, TimeoutException):
        print('Horse not found')
        if not retry:
            return sporting_index_bet(driver,
                                      race,
                                      retry=True,
                                      make_betfair_ew=make_betfair_ew)
        output_race(race, bet_made=False)
        return race, False

    if cur_odd_price == '':
        if not retry:
            return sporting_index_bet(driver,
                                      race,
                                      retry=True,
                                      make_betfair_ew=make_betfair_ew)
        output_race(race, bet_made=False)
        print('cur_odd_price is an empty string')

    cur_odd_price_frac = cur_odd_price.split('/')
    cur_odd_price = int(cur_odd_price_frac[0]) / int(cur_odd_price_frac[1]) + 1
    race['balance'] = get_balance_sporting_index(driver)
    if make_betfair_ew:
        race['ew_stake'] = race['bookie_stake']
    else:
        race['ew_stake'], race['expected_return'], race[
            'expected_value'] = kelly_criterion(race['horse_odds'],
                                                race['lay_odds'],
                                                race['lay_odds_place'],
                                                race['place'], race['balance'])
    if race['ew_stake'] < 0.1:
        output_race(race, bet_made=False)
        print('Stake is too small')
        return race, False

    if float(cur_odd_price) == float(race['horse_odds']):
        bet_made = make_sporting_index_bet(driver, race)
        if not make_betfair_ew:
            output_race(race, bet_made)
            if not bet_made:
                print('Odds have changed')
    else:
        print(
            f"Odds have changed - before: {float(race['horse_odds'])} after: {float(cur_odd_price)}\n"
        )
        WebDriverWait(driver, 60).until(
            EC.element_to_be_clickable(
                (By.XPATH,
                 "//li[@class='close']//wgt-spin-icon[@class='close-bet']"
                 ))).click()
        # driver.find_element_by_xpath(
        #     "//li[@class='close']//wgt-spin-icon[@class='close-bet']").click()
        return race, False
    return race, bet_made


def setup_sporting_index(driver):
    driver.get(
        'https://www.sportingindex.com/fixed-odds/horse-racing/race-calendar')
    balance = get_balance_sporting_index(driver)
    return {'balance': balance}
