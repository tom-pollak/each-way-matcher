import sys
import os
from time import time

from dotenv import load_dotenv
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import (
    WebDriverException,
    TimeoutException,
    StaleElementReferenceException,
    NoSuchElementException,
    ElementClickInterceptedException,
)

from matcher.exceptions import MatcherError
from matcher.calculate import check_start_time
import matcher.sites.betfair as betfair

BASEDIR = os.path.abspath(os.path.dirname(__file__) + "/../")
load_dotenv(os.path.join(BASEDIR, ".env"))
USERNAME = os.environ.get("S_INDEX_USER")
PASS = os.environ.get("S_INDEX_PASS")


def login(driver):
    driver.execute_script(
        """window.open("https://www.sportingindex.com/fixed-odds","_blank");"""
    )

    driver.switch_to.window(driver.window_handles[1])
    try:
        WebDriverWait(driver, 60).until(
            EC.visibility_of_element_located((By.ID, "usernameCompact"))
        ).send_keys(USERNAME)
    except TimeoutException:
        raise MatcherError("Couldn't login to Sporting Index")
    driver.find_element_by_id("passwordCompact").send_keys(PASS)
    driver.find_element_by_id("submitLogin").click()
    print("Logged in")
    sys.stdout.flush()


def change_to_decimal(driver):
    WebDriverWait(driver, 60).until(
        EC.element_to_be_clickable((By.XPATH, '//a[@class="btn-my-account"]'))
    ).click()
    WebDriverWait(driver, 60).until(
        EC.element_to_be_clickable((By.ID, "decimalBtn"))
    ).click()


def get_balance(driver):
    driver.switch_to.window(driver.window_handles[1])
    driver.refresh()
    for _ in range(5):
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
        except WebDriverException:
            driver.refresh()
    raise MatcherError("Couldn't get balance")


def refresh(driver):
    driver.switch_to.window(driver.window_handles[1])
    driver.refresh()
    try:
        WebDriverWait(driver, 60).until(
            EC.visibility_of_element_located(
                (By.XPATH, "/html/body/cmp-app/div/div/div/div/header[1]/wgt-logo/a")
            )
        )
    except TimeoutException:
        raise MatcherError("Timeout refreshing sporting index")


def click_betslip(driver):
    driver.refresh()
    try:
        WebDriverWait(driver, 60).until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "/html/body/cmp-app/div/ng-component/wgt-fo-top-navigation/nav/ul/li[14]/a",
                )
            )
        ).click()
    except (ElementClickInterceptedException, StaleElementReferenceException):
        raise MatcherError("Couldn't click betslip")


def place_bet(driver, race):
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


def get_page(driver, race):
    driver.switch_to.window(driver.window_handles[1])
    try:
        driver.get(race["bookie_exchange"])
        WebDriverWait(driver, 60).until(
            EC.visibility_of_element_located(
                (By.XPATH, "/html/body/cmp-app/div/div/div/div/header[1]/wgt-logo/a")
            )
        )
    except TimeoutException:
        raise MatcherError("Timeout getting sporting index page")


def make_bet(driver, race, market_ids=None, selection_id=None, lay=False):
    def click_horse(driver, horse_name):
        horse_name_xpath = f"//td[contains(text(), '{horse_name}')]/following-sibling::td[5]/wgt-price-button/button"
        try:
            horse_button = WebDriverWait(driver, 30).until(
                EC.element_to_be_clickable((By.XPATH, horse_name_xpath))
            )
            cur_odd_price = horse_button.text
            if cur_odd_price not in ["", "SUSP"]:
                horse_button.click()
                return cur_odd_price
        except NoSuchElementException:
            return None
        except (StaleElementReferenceException, TimeoutException):
            pass
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

    get_page(driver, race)
    cur_odd_price = click_horse(driver, race["horse_name"])
    if cur_odd_price is None:
        return None
    if not cur_odd_price:
        return False
    cur_odd_price_frac = cur_odd_price.split("/")
    cur_odd_price = round(
        int(cur_odd_price_frac[0]) / int(cur_odd_price_frac[1]) + 1, 2
    )

    if float(cur_odd_price) == race["bookie_odds"]:
        if lay:
            if market_ids is None:
                raise MatcherError("market_ids are None")
            if not betfair.check_odds(
                race, market_ids, selection_id
            ) or not check_start_time(race, secs=20):
                return False
        bet_made = place_bet(driver, race)
        if bet_made:
            return True
        close_bet(driver)
    return False
