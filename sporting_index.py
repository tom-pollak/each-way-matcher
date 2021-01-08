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


def output_race(driver, race):
    balance = get_balance_sporting_index(driver)
    print(f"\nBet made: {race['horse_name']} - {race['horse_odds']}")
    print(f"\tLay win: {race['lay_odds']} Lay place: {race['lay_odds_place']}")
    try:
        print(
            f"\tExpected value: {race['expected_value']}, Expected return: {race['expected_return']}"
        )
    except KeyError:
        print('Key Error in output_race')
    print(f"\t{race['date_of_race']} - {race['race_venue']}")
    print(f"\tCurrent balance: {balance}, stake: {race['ew_stake']}\n")


def get_balance_sporting_index(driver, retry=False):
    driver.switch_to.window(driver.window_handles[1])
    try:
        balance = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located(
                (By.CLASS_NAME, 'btn-balance'))).text
        count = 0
        while balance == 'BALANCE' and count < 10:
            sleep(0.5)
            balance = driver.find_element_by_class_name('btn-balance').text
            count += 1
        if balance == 'BALANCE':
            raise TypeError()
    except (NoSuchElementException, TimeoutException):
        if not retry:
            driver.refresh()
            balance = get_balance_sporting_index(driver, retry=True)
        else:
            raise Exception("Couldn't find balance %s" % count)

    balance = balance.replace(' ', '')
    balance = balance.replace('£', '')
    balance = balance.replace('▸', '')
    return float(balance)


def refresh_sporting_index(driver):
    driver.switch_to.window(driver.window_handles[1])
    sleep(0.1)
    driver.refresh()


def make_sporting_index_bet(driver, race):
    for _ in range(3):
        try:
            WebDriverWait(driver, 60).until(
                EC.element_to_be_clickable(
                    (By.CLASS_NAME,
                     'ng-pristine'))).send_keys(str(race['ew_stake']))
            break
        except (TimeoutException, StaleElementReferenceException):
            driver.refresh()
    else:
        return False

    driver.find_element_by_xpath('// input[ @ type = "checkbox"]').click()
    try:
        # WebDriverWait(driver, 60).until(
        #     EC.element_to_be_clickable(
        #         (By.CLASS_NAME, 'placeBetBtn'))).click()
        # driver.find_element_by_class_name('placeBetBtn').click()
        WebDriverWait(driver, 120).until(
            EC.element_to_be_clickable(
                (By.CLASS_NAME, 'placeBetBtn'))).click()
    except (NoSuchElementException, StaleElementReferenceException):
        driver.find_element_by_xpath(
            "//li[@class='close']//wgt-spin-icon[@class='close-bet']").click()
        return False

    try:
        WebDriverWait(driver, 60).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(text(), 'Continue')]"))).click()

    except (TimeoutException, StaleElementReferenceException):
        driver.refresh()
    return True


def get_sporting_index_page(driver, race):
    driver.switch_to.window(driver.window_handles[1])
    driver.get(race['bookie_exchange'])
    # driver.get(
    #     'https://www.sportingindex.com/fixed-odds/horse-racing/race-calendar')
    # WebDriverWait(driver, 60).until(
    #     EC.presence_of_element_located((
    #         By.XPATH,
    #         f"//th[contains(text(), '{race['race_venue']}')]/../../../tbody/tr/td/span/a/strong[contains(text(), '{race['race_time']}')]/.."
    #     ))).click()


def sporting_index_bet(driver, race, retry=False, make_betfair_ew=False):
    bet_made = False
    get_sporting_index_page(driver, race)
    horse_name_xpath = f"//td[contains(text(), '{race['horse_name']}')]/following-sibling::td[5]/wgt-price-button/button"
    try:
        for _ in range(5):
            try:
                horse_button = WebDriverWait(driver, 60).until(
                    EC.presence_of_element_located(
                        (By.XPATH, horse_name_xpath)))
                cur_odd_price = horse_button.text
                if cur_odd_price not in ['', 'SUSP']:
                    horse_button.click()
                    break
                sleep(1)
            except StaleElementReferenceException:
                driver.refresh()
        else:
            raise NoSuchElementException

    except (NoSuchElementException, TimeoutException):
        if not retry:
            return sporting_index_bet(driver,
                                      race,
                                      retry=True,
                                      make_betfair_ew=make_betfair_ew)
        print('Horse not found')
        return race, False

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
        print(f"Stake is too small: {race['ew_stake']}")
        return race, False

    if float(cur_odd_price) == float(race['horse_odds']):
        bet_made = make_sporting_index_bet(driver, race)
        if not bet_made:
            print('Odds have changed')
    else:
        print('Odds have changed')
        for _ in range(3):
            try:
                WebDriverWait(driver, 60).until(
                    EC.element_to_be_clickable((
                        By.XPATH,
                        "//li[@class='close']//wgt-spin-icon[@class='close-bet']"
                    ))).click()
                break
            except (TimeoutException, StaleElementReferenceException):
                driver.refresh()
    return race, bet_made


def setup_sporting_index(driver):
    driver.get(
        'https://www.sportingindex.com/fixed-odds/horse-racing/race-calendar')
    balance = get_balance_sporting_index(driver)
    return {'balance': balance}
