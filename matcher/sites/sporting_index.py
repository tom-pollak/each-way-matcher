from time import sleep

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import (
    WebDriverException,
    TimeoutException,
    StaleElementReferenceException,
    NoSuchElementException,
)

from matcher.exceptions import MatcherError
from matcher.calculate import check_odds_changes
from .betfair_api import get_race_odds


def change_to_decimal(driver):
    WebDriverWait(driver, 60).until(
        EC.element_to_be_clickable((By.XPATH, '//a[@class="btn-my-account"]'))
    ).click()
    WebDriverWait(driver, 60).until(
        EC.element_to_be_clickable((By.ID, "decimalBtn"))
    ).click()


def get_balance_sporting_index(driver):
    driver.switch_to.window(driver.window_handles[1])
    driver.refresh()
    for _ in range(10):
        try:
            balance = (
                WebDriverWait(driver, 15)
                .until(EC.visibility_of_element_located((By.CLASS_NAME, "btn-balance")))
                .text
            )
            balance = balance.replace(" ", "")
            balance = balance.replace("▸", "")
            balance = balance.replace("£", "")
            if balance not in ["BALANCE", ""]:
                return float(balance)
        except (NoSuchElementException, TimeoutException):
            driver.refresh()
    raise MatcherError("Couldn't get balance")


def refresh_sporting_index(driver):
    driver.switch_to.window(driver.window_handles[1])
    driver.refresh()
    WebDriverWait(driver, 60).until(
        EC.visibility_of_element_located(
            (By.XPATH, "/html/body/cmp-app/div/div/div/div/header[1]/wgt-logo/a")
        )
    )


def click_betslip(driver):
    driver.refresh()
    WebDriverWait(driver, 60).until(
        EC.element_to_be_clickable(
            (
                By.XPATH,
                "/html/body/cmp-app/div/ng-component/wgt-fo-top-navigation/nav/ul/li[14]/a",
            )
        )
    ).click()


def make_sporting_index_bet(driver, race):
    try:
        WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "ng-pristine"))
        ).send_keys(str(race["bookie_stake"]))
        driver.find_element_by_xpath('// input[ @ type = "checkbox"]').click()
        WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "placeBetBtn"))
        ).click()

        WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(text(), 'Continue')]")
            )
        ).click()
        return True

    except WebDriverException:
        return False


def get_sporting_index_page(driver, race):
    driver.switch_to.window(driver.window_handles[1])
    driver.get(race["bookie_exchange"])
    WebDriverWait(driver, 60).until(
        EC.visibility_of_element_located(
            (By.XPATH, "/html/body/cmp-app/div/div/div/div/header[1]/wgt-logo/a")
        )
    )


def sporting_index_bet(driver, race, market_ids=None, betfair=False):
    def click_horse(driver, horse_name):
        horse_name_xpath = f"//td[contains(text(), '{horse_name}')]/following-sibling::td[5]/wgt-price-button/button"
        for _ in range(5):
            try:
                horse_button = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, horse_name_xpath))
                )
                cur_odd_price = horse_button.text
                if cur_odd_price not in ["", "SUSP"]:
                    horse_button.click()
                    return cur_odd_price
            except (StaleElementReferenceException, TimeoutException):
                driver.refresh()
            except NoSuchElementException:
                return None
        return False

    def close_bet(driver):
        try:
            WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        '//*[@id="top"]/wgt-betslip/div/div/div/wgt-bet-errors/div/div/button[1]',
                    )
                )
            ).click()
            return
        except TimeoutException:
            pass
        try:
            click_betslip(driver)
            WebDriverWait(driver, 10).until(
                (
                    EC.element_to_be_clickable(
                        (
                            By.XPATH,
                            '//*[@id="top"]/wgt-betslip/div/div/div/wgt-bet-errors/div/div/button',
                        )
                    )
                )
            )
            return
        except TimeoutException:
            pass

    get_sporting_index_page(driver, race)
    cur_odd_price = click_horse(driver, race["horse_name"])
    if cur_odd_price is None:
        return race, None
    if not cur_odd_price:
        return race, False
    cur_odd_price_frac = cur_odd_price.split("/")
    cur_odd_price = int(cur_odd_price_frac[0]) / int(cur_odd_price_frac[1]) + 1

    if float(cur_odd_price) == float(race["bookie_odds"]):
        if betfair:
            if market_ids is None:
                raise MatcherError("market_ids are None")
            win_horse_odds = get_race_odds(market_ids["Win"])
            place_horse_odds = get_race_odds(market_ids["Place"])
            if check_odds_changes(race, win_horse_odds, place_horse_odds):
                return race, False
        bet_made = make_sporting_index_bet(driver, race)
        if bet_made:
            return race, True
        close_bet(driver)
    return race, False


def setup_sporting_index(driver):
    driver.get("https://www.sportingindex.com/fixed-odds/horse-racing/race-calendar")