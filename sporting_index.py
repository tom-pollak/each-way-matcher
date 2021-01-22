from time import sleep
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException, NoSuchElementException, ElementNotInteractableException


def change_to_decimal(driver):
    WebDriverWait(driver, 60).until(
        EC.element_to_be_clickable(
            (By.XPATH, '//a[@class="btn-my-account"]'))).click()
    WebDriverWait(driver,
                  60).until(EC.element_to_be_clickable(
                      (By.ID, 'decimalBtn'))).click()


def output_race(driver, race):
    balance = get_balance_sporting_index(driver)
    print(f"\nEW no lay bet made: {race['horse_name']} - {race['horse_odds']}")
    print(f"\tLay win: {race['lay_odds']} Lay place: {race['lay_odds_place']}")
    try:
        print(
            f"\tExpected value: {race['expected_value']}, Expected return: {race['expected_return']}"
        )
    except KeyError:
        print('Key Error in output_race')
    print(f"\t{race['date_of_race']} - {race['race_venue']}")
    print(f"\tCurrent balance: {balance}, stake: {race['ew_stake']}\n")


def get_balance_sporting_index(driver):
    driver.switch_to.window(driver.window_handles[1])
    sleep(3)
    try:
        count = 0
        balance = 'BALANCE'
        while balance in ['BALANCE', ''] and count < 10:
            sleep(1)
            balance = WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located(
                    (By.CLASS_NAME, 'btn-balance'))).text
            balance = balance.replace(' ', '')
            balance = balance.replace('▸', '')
            balance = balance.replace('£', '')
            count += 1
        if balance in ['BALANCE', '']:
            raise ValueError('balance is BALANCE')

    except (NoSuchElementException, TimeoutException):
        raise ValueError("Couldn't find balance %s" % count)
    return float(balance)


def refresh_sporting_index(driver):
    driver.switch_to.window(driver.window_handles[1])
    sleep(0.1)
    driver.refresh()


def click_betslip(driver):
    driver.refresh()
    WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((
            By.XPATH,
            '/html/body/cmp-app/div/ng-component/wgt-fo-top-navigation/nav/ul/li[14]/a'
        ))).click()


def make_sporting_index_bet(driver, race, retry=False):
    for _ in range(3):
        try:
            WebDriverWait(driver, 60).until(
                EC.element_to_be_clickable(
                    (By.CLASS_NAME,
                     'ng-pristine'))).send_keys(str(race['ew_stake']))
            break
        except (StaleElementReferenceException,
                ElementNotInteractableException):
            click_betslip(driver)
        except TimeoutException:
            if not retry:
                click_betslip(driver)
                return make_sporting_index_bet(driver, race, retry=True)
            return False
    else:
        return False

    try:
        driver.find_element_by_xpath('// input[ @ type = "checkbox"]').click()
        WebDriverWait(driver, 120).until(
            EC.element_to_be_clickable(
                (By.CLASS_NAME, 'placeBetBtn'))).click()
    except (NoSuchElementException, StaleElementReferenceException):
        # driver.find_element_by_xpath(
        #     "//li[@class='close']//wgt-spin-icon[@class='close-bet']").click()
        return False
    except TimeoutException:
        if not retry:
            click_betslip(driver)
            return make_sporting_index_bet(driver, race, retry=True)
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


def sporting_index_bet(driver, race, make_betfair_ew=False):
    if make_betfair_ew:
        race['ew_stake'] = race['bookie_stake']

    def click_horse(driver, horse_name):
        horse_name_xpath = f"//td[contains(text(), '{horse_name}')]/following-sibling::td[5]/wgt-price-button/button"
        for _ in range(5):
            try:
                horse_button = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located(
                        (By.XPATH, horse_name_xpath)))
                cur_odd_price = horse_button.text
                if cur_odd_price not in ['', 'SUSP']:
                    horse_button.click()
                    return cur_odd_price
                sleep(2)
            except (StaleElementReferenceException, TimeoutException):
                driver.refresh()
            except NoSuchElementException:
                return None
        return False

    def close_bet(driver, retry=False):
        try:
            WebDriverWait(driver, 60).until(
                EC.element_to_be_clickable((
                    By.XPATH,
                    # '//*[@id="top"]/wgt-betslip/div/div/div/div/div/div/div/wgt-single-bet/ul/li[5]/wgt-spin-icon'
                    '//*[@id="top"]/wgt-betslip/div/div/div/wgt-bet-errors/div/div/button[1]'
                    # "//li[@class='close']//wgt-spin-icon[@class='close-bet']"
                ))).click()
        except TimeoutException:
            if not retry:
                click_betslip(driver)
                close_bet(driver, retry=True)

    bet_made = False
    get_sporting_index_page(driver, race)
    cur_odd_price = click_horse(driver, race['horse_name'])
    if cur_odd_price is None:
        return race, None
    if not cur_odd_price:
        return race, False
    cur_odd_price_frac = cur_odd_price.split('/')
    cur_odd_price = int(cur_odd_price_frac[0]) / int(cur_odd_price_frac[1]) + 1

    if float(cur_odd_price) == float(race['horse_odds']):
        bet_made = make_sporting_index_bet(driver, race)
        if not bet_made:
            close_bet(driver)
        driver.refresh()
        sleep(5)
    return race, bet_made


def setup_sporting_index(driver):
    driver.get(
        'https://www.sportingindex.com/fixed-odds/horse-racing/race-calendar')
