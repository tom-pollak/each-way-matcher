import requests
from bs4 import BeautifulSoup
import pandas as pd

from .run import setup_selenium


def get_odds(market_id):
    driver = setup_selenium()
    driver.get(
        "https://www.betfair.com/exchange/plus/horse-racing/market/%s" % market_id,
    )
    soup = BeautifulSoup(driver.page_source, "html.parser")
    table = soup.find_all("table", class_="mv-runner-list")
    print(res.text)
