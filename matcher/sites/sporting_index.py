import sys
import os

# debug
import traceback
from datetime import datetime

from dotenv import load_dotenv
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import (
    WebDriverException,
    TimeoutException,
    StaleElementReferenceException,
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
    if len(driver.window_handles) == 1:
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


def change_to_decimal(driver):
    WebDriverWait(driver, 60).until(
        EC.element_to_be_clickable((By.XPATH, '//a[@class="btn-my-account"]'))
    ).click()
    WebDriverWait(driver, 60).until(
        EC.element_to_be_clickable((By.ID, "decimalBtn"))
    ).click()


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


def get_balance(driver):
    driver.switch_to.window(driver.window_handles[1])
    refresh(driver)
    try:
        balance = (
            WebDriverWait(driver, 15)
            .until(EC.visibility_of_element_located((By.CLASS_NAME, "btn-balance")))
            .text
        )
    except WebDriverException:
        print("Couldn't get balance (not logged in?)")
        driver.save_screenshot("failed-get-balance.png")
        login(driver)
        return get_balance(driver)
        # raise MatcherError("Error getting Sporting Index balance")

    balance = balance.replace(" ", "")
    balance = balance.replace("▸", "")
    balance = balance.replace("£", "")
    if balance not in ["BALANCE", ""]:
        return float(balance)

    driver.save_screenshot("failed-get-balance.png")
    raise MatcherError("Couldn't get Sporting Index balance")


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


def click_betslip(driver):
    # betslip clicked
    try:
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located(
                (By.XPATH, '//*[@id="top"]/wgt-betslip/div/div')
            )
        )

    # click betslip
    except TimeoutException:
        try:
            WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "/html/body/cmp-app/div/ng-component/wgt-fo-top-navigation/nav/ul/li[15]/a",
                    )
                )
            ).click()
        except (ElementClickInterceptedException, StaleElementReferenceException):
            raise MatcherError("Couldn't click betslip")


def click_horse(driver, horse_name):
    horse_name_xpath = f"//td[contains(text(), '{horse_name}')]/following-sibling::td[5]/wgt-price-button/button"
    try:
        horse_button = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.XPATH, horse_name_xpath))
        )
        cur_odd_price = horse_button.text
        if cur_odd_price != "SUSP":
            horse_button.click()
            return True
        print("Horse is SUSP")
    except WebDriverException:
        pass
    return False


def get_odds(driver):
    # click accept changes
    try:
        WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    '//*[@id="top"]/wgt-betslip/div/div/div/wgt-price-change-message/div/p/button',
                )
            )
        ).click()
    except WebDriverException:
        pass

    try:
        frac_odd = (
            WebDriverWait(driver, 10)
            .until(
                EC.visibility_of_element_located(
                    (
                        By.XPATH,
                        '//*[@id="top"]/wgt-betslip/div/div/div/div/div/div/div/wgt-single-bet/ul/li[1]/span[2]/wgt-live-price-raw',
                    )
                )
            )
            .text.split("/")
        )
    except TimeoutException:
        driver.save_screenshot("failed-getting-odds.png")
        return False
    return round(int(frac_odd[0]) / int(frac_odd[1]) + 1, 2)


def close_bet(driver):
    click_betslip(driver)
    try:
        WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    '//*[@id="top"]/wgt-betslip/div/div/div/wgt-bet-errors/div/div/button[1]',
                )
            )
        ).click()
    except TimeoutException:
        try:
            WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        '//*[@id="top"]/wgt-betslip/div/div/div/wgt-bet-errors/div/div/button',
                    )
                )
            ).click()
        except TimeoutException:
            print("Failed to close bet")


def place_bet(driver, race):
    try:
        WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    '//*[@id="top"]/wgt-betslip/div/div/div/div/div/div/div/wgt-single-bet/ul/li[1]/span[3]/input',
                )
            )
        ).send_keys(str(race["bookie_stake"]))
        driver.find_element_by_xpath('//input[@type="checkbox"]').click()
        # can timeout if the race has started
        WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "placeBetBtn"))
        ).click()

        # continue button
        try:
            WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        '//*[@id="top"]/wgt-betslip/div/wgt-bet-placement/div/p/button[1]',
                    )
                )
            ).click()
        except TimeoutException:
            driver.save_screenshot("stake-limited.png")
            print("Account stake limited!")
            return False
        except ElementClickInterceptedException:
            print("Error placing bet, retrying...")
            return "retry"
        return True

    except WebDriverException:
        print("Bet failed:\n%s\n\n%s" % (race, traceback.format_exc()))
        driver.save_screenshot("failed-bet.png")
        return False


def make_bet(driver, race, market_ids=None, selection_id=None, lay=False):
    get_page(driver, race)
    clicked = click_horse(driver, race["horse_name"])
    if not clicked:
        print(
            f"\nHorse not found: {race['horse_name']}  venue: {race['venue']}  race time: {race['race_time']} - {datetime.now()}"
        )
        return False

    cur_odd_price = get_odds(driver)
    if not cur_odd_price:
        print("Couldn't get horse odds")

    elif float(cur_odd_price) >= float(race["bookie_odds"]):
        race["bookie_odds"] = cur_odd_price
        if lay:
            if market_ids is None:
                raise MatcherError("market_ids are None")
            if not betfair.check_odds(
                race, market_ids, selection_id
            ) or not check_start_time(race, secs=20):
                return False

        bet_made = place_bet(driver, race)
        if bet_made == "retry":
            return make_bet(
                driver, race, market_ids=market_ids, selection_id=selection_id, lay=lay
            )
        if bet_made:
            return True

    close_bet(driver)
    return False
