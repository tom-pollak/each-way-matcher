import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException


def get_site(driver, market_id, tab=0):
    driver.switch_to.window(driver.window_handles[tab])
    driver.get(
        "https://www.betfair.com/exchange/plus/horse-racing/market/%s" % str(market_id),
    )
    time.sleep(0.53)
    WebDriverWait(driver, 60).until(
        EC.element_to_be_clickable((By.XPATH, '//*[@id="onetrust-accept-btn-handler"]'))
    ).click()
    driver.switch_to.default_content()


def scrape_odds(driver, tab):
    driver.switch_to.window(driver.window_handles[tab])
    horses = {}
    soup = BeautifulSoup(driver.page_source, "html.parser")
    table = soup.find_all("table", class_="mv-runner-list")[1]
    runners = table.find_all("tr", class_="runner-line")
    for runner in runners:
        name = runner.find("h3", class_="runner-name").contents[0]
        horses[name] = {}
        back_odds_buttons = runner.find_all("td", class_="back-cell")[::-1]
        lay_odds_buttons = runner.find_all("td", class_="lay-cell")
        for i, (back_button, lay_button) in enumerate(
            zip(back_odds_buttons, lay_odds_buttons)
        ):
            back_odds = float(back_button.find("span", class_="bet-button-price").text)
            lay_odds = float(lay_button.find("span", class_="bet-button-price").text)
            back_availiable = float(
                back_button.find("span", class_="bet-button-size").text.replace("£", "")
            )
            lay_avaliable = float(
                lay_button.find("span", class_="bet-button-size").text.replace("£", "")
            )
            horses[name]["back_odds_%s" % str(i + 1)] = back_odds
            horses[name]["lay_odds_%s" % str(i + 1)] = lay_odds
            horses[name]["back_avaliable_%s" % str(i + 1)] = back_availiable
            horses[name]["lay_avaliable_%s" % str(i + 1)] = lay_avaliable
    return horses
