from time import sleep
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException

from calculate_odds import kelly_criterion


def change_to_decimal(driver):
    WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable(
            (By.XPATH, '//a[@class="btn-my-account"]'))).click()
    # driver.find_element_by_xpath('//a[@class="btn-my-account"]').click()
    WebDriverWait(driver,
                  30).until(EC.element_to_be_clickable(
                      (By.ID, 'decimalBtn'))).click
    # driver.find_element_by_id('decimalBtn').click()
    sleep(0.5)


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
    change_to_decimal(driver)


def make_sporting_index_bet(driver, race, RETURNS_CSV):
    success = True
    driver.find_element_by_class_name('ng-pristine').send_keys(
        str(race['ew_stake']))
    driver.find_element_by_xpath('// input[ @ type = "checkbox"]').click()
    try:
        driver.find_element_by_class_name('placeBetBtn').click()
    except NoSuchElementException:
        print('Odds have changed')
        driver.find_element_by_xpath(
            "//li[@class='close']//wgt-spin-icon[@class='close-bet']").click()
        success = False

    el = WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(text(), 'Continue')]")))
    el.click()
    print('Bet made\n')
    driver.refresh()
    change_to_decimal(driver)
    driver.find_element_by_xpath(
        "//li[@class='close']//wgt-spin-icon[@class='close-bet']").click()
    return success


def get_sporting_index_page(driver, race):
    driver.switch_to.window(driver.window_handles[1])
    driver.refresh()
    change_to_decimal(driver)
    WebDriverWait(driver, 60).until(
        EC.presence_of_element_located((
            By.XPATH,
            f"//th[contains(text(), '{race['race_venue']}')]/../../../tbody/tr/td/span/a/strong[contains(text(), '{race['race_time']}')]/.."
        ))).click()


def sporting_index_bet(driver, race, RETURNS_CSV):
    get_sporting_index_page(driver, race)
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CLASS_NAME, 'horseName')))
    horse_name_xpath = f"//td[contains(text(), '{race['horse_name']}')]/following-sibling::td[5]/wgt-price-button/button"
    driver.find_element_by_xpath(horse_name_xpath).click()

    cur_odd_price = WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.TAG_NAME, 'wgt-live-price-raw')))
    if cur_odd_price != '':
        race['balance'] = get_balance_sporting_index(driver)
        race['ew_stake'], race['expected_return'], race['expected_value'] = kelly_criterion(race['horse_odds'], race['lay_odds'], race['lay_odds_place'], race['place'], race['balance'])
        if race['ew_stake'] < 0.1:
            print(f"Odds are too small to bet - {race['ew_stake']}")
            return race, False
        print(cur_odd_price.text, race['horse_odds'])
        if float(cur_odd_price.text) == float(race['horse_odds']):
            bet_made = make_sporting_index_bet(driver, race, RETURNS_CSV)
        else:
            print(
                f"Odds have changed - before: {float(race['horse_odds'])} after: {float(cur_odd_price.text)}\n"
            )
            driver.find_element_by_xpath(
                "//li[@class='close']//wgt-spin-icon[@class='close-bet']"
            ).click()
            bet_made = False
    else:
        print('cur_odd_price is an empty string')
        bet_made = False
    driver.get(
        'https://www.sportingindex.com/fixed-odds/horse-racing/race-calendar')
    return race, bet_made


def setup_sporting_index(driver):
    driver.get(
        'https://www.sportingindex.com/fixed-odds/horse-racing/race-calendar')
    change_to_decimal(driver)
    balance = get_balance_sporting_index(driver)
    return {'balance': balance}
