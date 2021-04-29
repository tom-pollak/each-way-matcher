import os
import sys
import shutil
from datetime import datetime
from dotenv import load_dotenv
from selenium import webdriver

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    TimeoutException,
    ElementClickInterceptedException,
)

from .exceptions import MatcherError

BASEDIR = os.path.abspath(os.path.dirname(__file__) + "/../")
load_dotenv(os.path.join(BASEDIR, ".env"))

RETURNS_CSV = os.environ.get("RETURNS_CSV")
ODD_M_USER = os.environ.get("ODD_M_USER")
ODD_M_PASS = os.environ.get("ODD_M_PASS")
APP_KEY = os.environ.get("APP_KEY")
BETFAIR_USR = os.environ.get("BETFAIR_USR")
BETFAIR_PASS = os.environ.get("BETFAIR_PASS")
BETFAIR_CERT = os.path.join(BASEDIR, "client-2048.crt")
BETFAIR_KEY = os.path.join(BASEDIR, "client-2048.key")
S_INDEX_USER = os.environ.get("S_INDEX_USER")
S_INDEX_PASS = os.environ.get("S_INDEX_PASS")


def check_vars():
    if None in (
        ODD_M_USER,
        ODD_M_PASS,
        S_INDEX_USER,
        S_INDEX_PASS,
        BETFAIR_USR,
        BETFAIR_PASS,
        BETFAIR_CERT,
        BETFAIR_KEY,
    ):
        raise Exception(
            "ERROR: Oddsmonkey, SportingIndex or BetFair env variables not set"
        )


def setup_selenium():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (X11; CrOS x86_64 8172.45.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.64 Safari/537.36"
    )
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-setuid-sandbox")
    chrome_options.add_argument("--remote-debugging-port=9222")  # this
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-browser-side-navigation")
    chrome_options.add_argument("--disable-features=VizDisplayCompositor")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("start-maximized")
    prefs = {"profile.default_content_setting_values.notifications": 2}
    chrome_options.add_experimental_option("prefs", prefs)
    return webdriver.Chrome(options=chrome_options)


def reset_csv():
    if not os.path.isdir("stats"):
        os.mkdir("stats")
    if not os.path.isfile(".env"):
        shutil.copyfile(".env.template", ".env")
    now = datetime.now().strftime("%d-%m-%Y")
    RETURNS_HEADER = "current_time,date_of_race,venue,horse_name,exp_value,exp_growth,exp_return,bookie_stake,bookie_odds,win_stake,win_odds,place_stake,place_odds,bookie_balance,betfair_balance,win_profit,place_profit,lose_profit,bet_type,place_payout\n"
    RETURNS_BAK = os.path.join(BASEDIR, "stats/returns-%s.csv" % now)
    create_new_returns = "y"

    if os.path.isfile(RETURNS_CSV):
        create_new_returns = input(
            "Create new return.csv? (Recommended for new user) Y/[n] "
        ).lower()

    if create_new_returns == "y":
        if os.path.isfile(RETURNS_CSV):
            count = 2
            while os.path.isfile(RETURNS_BAK):
                RETURNS_BAK = f"{RETURNS_BAK}({str(count)})"
                count += 1
            os.rename(RETURNS_CSV, RETURNS_BAK)
        with open(RETURNS_CSV, "w", newline="") as returns_csv:
            returns_csv.write(RETURNS_HEADER)
            print("Created new returns.csv")
