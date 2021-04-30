import os
from datetime import datetime

from dotenv import load_dotenv
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    ElementClickInterceptedException,
    NoSuchFrameException,
    NoSuchWindowException,
    ElementNotInteractableException,
)

from matcher.exceptions import MatcherError

BASEDIR = os.path.abspath(os.path.dirname(__file__) + "/../")
load_dotenv(os.path.join(BASEDIR, ".env"))

USERNAME = os.environ.get("ODD_M_USER")
PASS = os.environ.get("ODD_M_PASS")


def login(driver):
    driver.get("https://www.oddsmonkey.com/oddsmonkeyLogin.aspx?returnurl=%2f")
    try:
        WebDriverWait(driver, 60).until(
            EC.visibility_of_element_located(
                (By.ID, "dnn_ctr433_Login_Login_DNN_txtUsername")
            )
        ).send_keys(USERNAME)
    except TimeoutException:
        raise MatcherError("Couldn't login to Oddsmonkey")
    driver.find_element_by_id("dnn_ctr433_Login_Login_DNN_txtPassword").send_keys(PASS)
    driver.find_element_by_id("dnn_ctr433_Login_Login_DNN_cmdLogin").click()
    WebDriverWait(driver, 60).until(
        EC.visibility_of_element_located((By.XPATH, '//*[@id="mainTitle"]'))
    )

    driver.get("https://www.oddsmonkey.com/Tools/Matchers/EachwayMatcher.aspx")
    try:
        WebDriverWait(driver, 60).until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    '//*[@id="dnn_ctr1157_View_RadGrid1_ctl00"]/thead/tr/th[17]/a',
                )
            )
        ).click()
    except TimeoutException:
        print("Need Oddsmonkey premium membership (OM12FOR1)")
        raise KeyboardInterrupt
    except ElementClickInterceptedException:
        print("Dismiss one time pop-up boxes and setup oddsmonkey")
        raise KeyboardInterrupt


def find_races(driver, row=0, window=0):
    driver.switch_to.window(driver.window_handles[window])
    driver.switch_to.default_content()
    horse_name = driver.find_element_by_xpath(
        f'//table//tr[@id="dnn_ctr1157_View_RadGrid1_ctl00__{row}"]//td[9]'
    ).text.title()

    date_of_race = driver.find_element_by_xpath(
        f'//table//tr[@id="dnn_ctr1157_View_RadGrid1_ctl00__{row}"]//td[1]'
    ).text
    race_time = date_of_race[-5:].lower()
    date_of_race += " %s" % datetime.today().year
    venue = (
        driver.find_element_by_xpath(
            f'//table//tr[@id="dnn_ctr1157_View_RadGrid1_ctl00__{row}"]//td[8]'
        )
        .text.lower()
        .strip()
    )
    venue = venue[: len(venue) - 5].strip().title()

    bookie_odds = driver.find_element_by_xpath(
        f'//table//tr[@id="dnn_ctr1157_View_RadGrid1_ctl00__{row}"]//td[13]'
    ).text

    bookie_exchange = driver.find_element_by_xpath(
        f'//*[@id="dnn_ctr1157_View_RadGrid1_ctl00__{row}"]/td[10]/a'
    ).get_attribute("href")
    if "sportingindex" not in bookie_exchange:
        print("Bookie is not SportingIndex, have you adjusted the filters?")
        print(bookie_exchange)
        raise KeyboardInterrupt

    rating = driver.find_element_by_xpath(
        f'//*[@id="dnn_ctr1157_View_RadGrid1_ctl00__{row}"]/td[17]'
    ).text

    max_profit = driver.find_element_by_xpath(
        f'//*[@id="dnn_ctr1157_View_RadGrid1_ctl00__{row}"]/td[20]'
    ).text.split("£")[1]

    try:
        driver.find_element_by_xpath(
            f'//*[@id="dnn_ctr1157_View_RadGrid1_ctl00_ctl{"{:02d}".format(2 * row + 4)}_calcButton"]'
        ).click()
    except ElementNotInteractableException:
        raise MatcherError("Couldn't click calculator button")

    try:
        driver.switch_to.frame("RadWindow2")
    except NoSuchFrameException:
        raise MatcherError("Couldn't switch to calculator window find_races")

    try:
        horse_name_window = (
            WebDriverWait(driver, 60)
            .until(
                EC.visibility_of_element_located(
                    (By.XPATH, '//*[@id="lblOutcomeName"]')
                )
            )
            .text.title()
        )
    except (TimeoutException, NoSuchWindowException):
        raise MatcherError("Couldn't get calculator window")

    if horse_name != horse_name_window:
        raise MatcherError(
            "horse_name not same: %s, %s" % (horse_name, horse_name_window)
        )

    win_odds = (
        WebDriverWait(driver, 600)
        .until(
            EC.visibility_of_element_located((By.XPATH, '//*[@id="txtLayOdds_win"]'))
        )
        .get_attribute("value")
    )

    place_odds = driver.find_element_by_xpath(
        '//*[@id="txtLayOdds_place"]'
    ).get_attribute("value")
    places_paid = driver.find_element_by_xpath(
        '//*[@id="lblPlacesPaid_lay"]'
    ).get_attribute("value")
    place_payout = driver.find_element_by_xpath(
        '//*[@id="txtPlacePayout"]'
    ).get_attribute("value")

    bookie_stake = (
        WebDriverWait(driver, 15)
        .until(
            EC.visibility_of_element_located(
                (By.XPATH, '//*[@id="lblStep1"]/strong[1]')
            )
        )
        .text.replace("£", "")
    )

    win_stake = driver.find_element_by_xpath(
        '//*[@id="lblStep2"]/strong[1]'
    ).text.replace("£", "")
    place_stake = driver.find_element_by_xpath('//*[@id="lblStep3"]/b').text.replace(
        "£", ""
    )

    driver.switch_to.default_content()
    driver.find_element_by_class_name("rwCloseButton").click()

    return {
        "date_of_race": date_of_race,
        "race_time": race_time,
        "horse_name": horse_name,
        "bookie_odds": float(bookie_odds),
        "venue": venue,
        "bookie_exchange": bookie_exchange,
        "rating": float(rating),
        "current_time": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "win_odds": float(win_odds),
        "place_odds": float(place_odds),
        "places_paid": float(places_paid),
        "place_payout": float(place_payout),
        "bookie_stake": float(bookie_stake),
        "win_stake": float(win_stake),
        "place_stake": float(place_stake),
        "max_profit": float(max_profit),
    }


def hide_race(driver, row=0, window=0):
    driver.switch_to.window(driver.window_handles[window])
    driver.find_element_by_xpath(
        f'//table//tr[@id="dnn_ctr1157_View_RadGrid1_ctl00__{row}"]//td[55]//div//a'
    ).click()
    WebDriverWait(driver, 60).until(
        EC.invisibility_of_element_located(
            (By.ID, "dnn_ctr1157_View_RadAjaxLoadingPanel1dnn_ctr1157_View_RadGrid1")
        )
    )


def trigger_betfair_options(driver):
    WebDriverWait(driver, 60).until(
        EC.element_to_be_clickable(
            (By.XPATH, '//*[@id="dnn_ctr1157_View_RadGrid1_ctl00"]/thead/tr/th[17]/a')
        )
    ).click()

    WebDriverWait(driver, 60).until(
        EC.visibility_of_element_located(
            (
                By.XPATH,
                '//*[@id="dnn_ctr1157_View_RadToolBar1"]/div/div/div/ul/li[6]/a/span/span/span/span',
            )
        )
    ).click()
    WebDriverWait(driver, 60).until(
        EC.element_to_be_clickable((By.XPATH, '//*[@id="headingFour"]/h4/a'))
    ).click()
    driver.find_element_by_xpath(
        '//*[@id="dnn_ctr1157_View_rlbExchanges"]/div/div/label/input'
    ).click()
    driver.find_element_by_xpath(
        '//*[@id="dnn_ctr1157_View_rlbExchanges_i0"]/label/input'
    ).click()
    driver.find_element_by_xpath('//*[@id="dnn_ctr1157_View_btnApplyFilter"]').click()
    driver.find_element_by_xpath(
        '//*[@id="dnn_ctr1157_ModuleContent"]/div[10]/div[1]/a'
    ).click()


def refresh(driver, betfair=False):
    for _ in range(3):
        driver.switch_to.default_content()
        try:
            action = ActionChains(driver)
            try:
                element = WebDriverWait(driver, 30).until(
                    EC.visibility_of_element_located(
                        (
                            By.XPATH,
                            '//*[@id="dnn_ctr1157_View_RadGrid1_ctl00"]/thead/tr/th[2]',
                        )
                    )
                )
            except TimeoutException:
                raise MatcherError("Timout in refresh odds monkey")
            action.move_to_element(element)
            action.perform()

            WebDriverWait(driver, 30).until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        '//*[@id="dnn_ctr1157_View_RadToolBar1_i11_lblRefreshText"]',
                    )
                )
            ).click()
            # wait until spinner disappeared
            WebDriverWait(driver, 30).until(
                EC.invisibility_of_element_located(
                    (
                        By.ID,
                        "dnn_ctr1157_View_RadAjaxLoadingPanel1dnn_ctr1157_View_RadGrid1",
                    )
                )
            )
            return

        except (TimeoutException, ElementClickInterceptedException):
            driver.refresh()
            WebDriverWait(driver, 60).until(
                EC.visibility_of_element_located(
                    (By.XPATH, '//*[@id="dnn_LOGO1_imgLogo"]')
                )
            )
            if betfair:
                trigger_betfair_options(driver)
                driver.switch_to.default_content()
    raise MatcherError("Couldn't refresh Oddsmonkey")


def open_betfair_page(driver):
    driver.execute_script(
        """window.open("https://www.oddsmonkey.com/Tools/Matchers/EachwayMatcher.aspx","_blank");"""
    )
    driver.switch_to.window(driver.window_handles[2])
    trigger_betfair_options(driver)


def get_no_rows(driver):
    count = 0
    while True:
        try:
            driver.find_element_by_xpath(
                f'//table//tr[@id="dnn_ctr1157_View_RadGrid1_ctl00__{count}"]//td[1]'
            )
            count += 1
        except NoSuchElementException:
            return count
