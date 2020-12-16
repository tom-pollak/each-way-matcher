from time import sleep
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException, NoSuchElementException

from calculate_odds import kelly_criterion
from odds_monkey import output_race


def change_to_decimal(driver):
    WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable(
            (By.XPATH, '//a[@class="btn-my-account"]'))).click()
    WebDriverWait(driver,
                  30).until(EC.element_to_be_clickable(
                      (By.ID, 'decimalBtn'))).click


def get_balance_sporting_index(driver):
    driver.switch_to.window(driver.window_handles[1])
    balance = WebDriverWait(driver, 40).until(
        EC.visibility_of_element_located((By.CLASS_NAME, 'btn-balance'))).text
    balance = balance.replace(' ', '')
    balance = balance.replace('£', '')
    balance = balance.replace('▸', '')
    return float(balance)


def refresh_sporting_index(driver, count):
    driver.switch_to.window(driver.window_handles[1])
    sleep(0.1)
    driver.refresh()


def make_sporting_index_bet(driver, race):
    # success = True
    driver.find_element_by_class_name('ng-pristine').send_keys(
        str(race['ew_stake']))
    driver.find_element_by_xpath('// input[ @ type = "checkbox"]').click()
    try:
        driver.find_element_by_class_name('placeBetBtn').click()
    except NoSuchElementException:
        print('Odds have changed')
        driver.find_element_by_xpath(
            "//li[@class='close']//wgt-spin-icon[@class='close-bet']").click()
        return False
        # success = False

    el = WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(text(), 'Continue')]"))).click()
    return True
    # return success


def get_sporting_index_page(driver, race):
    driver.switch_to.window(driver.window_handles[1])
    driver.get(
        'https://www.sportingindex.com/fixed-odds/horse-racing/race-calendar')
    WebDriverWait(driver, 60).until(
        EC.presence_of_element_located((
            By.XPATH,
            f"//th[contains(text(), '{race['race_venue']}')]/../../../tbody/tr/td/span/a/strong[contains(text(), '{race['race_time']}')]/.."
        ))).click()


def sporting_index_bet(driver, race, recursive=False):
    get_sporting_index_page(driver, race)
    horse_name_xpath = f"//td[contains(text(), '{race['horse_name']}')]/following-sibling::td[5]/wgt-price-button/button"
    try:
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located(
                (By.XPATH, horse_name_xpath))).click()
    except NoSuchElementException:
        print('Horse not found')
        return sporting_index_bet(driver, race, recursive=True)

    # change_to_decimal(driver)
    try:
        cur_odd_price = WebDriverWait(driver, 60).until(
            EC.visibility_of_element_located((
                By.XPATH, # wgt-live-price-raw
                '//*[@id="top"]/wgt-betslip/div/div/div/div/div/div/div/wgt-single-bet/ul/li[1]/span[2]/wgt-live-price-raw'
            ))).text
    except (TimeoutException, StaleElementReferenceException):
        if not recursive:
            output_race(race, bet_made=False)
            print('Live price not found')
            return sporting_index_bet(driver, race, True)
        else:
            return race, False

    if cur_odd_price != '':
        cur_odd_price_frac = cur_odd_price.split('/')
        cur_odd_price = int(cur_odd_price_frac[0]) / int(
            cur_odd_price_frac[1]) + 1
        race['balance'] = get_balance_sporting_index(driver)
        race['ew_stake'], race['expected_return'], race['expected_value'] = kelly_criterion(race['horse_odds'], race['lay_odds'], race['lay_odds_place'], race['place'], race['balance'])
        if race['ew_stake'] < 0.1:
            return race, False
        if float(cur_odd_price) == float(race['horse_odds']):
            bet_made = make_sporting_index_bet(driver, race)
        else:
            output_race(race, bet_made=False)
            print(
                f"Odds have changed - before: {float(race['horse_odds'])} after: {float(cur_odd_price)}\n"
            )
            driver.find_element_by_xpath(
                "//li[@class='close']//wgt-spin-icon[@class='close-bet']"
            ).click()
            bet_made = False
    else:
        output_race(race, bet_made=False)
        print('cur_odd_price is an empty string')
        bet_made = False
    return race, bet_made


def setup_sporting_index(driver):
    driver.get(
        'https://www.sportingindex.com/fixed-odds/horse-racing/race-calendar')
    balance = get_balance_sporting_index(driver)
    return {'balance': balance}
