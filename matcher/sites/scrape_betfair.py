from bs4 import BeautifulSoup

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def setup_scrape_betfair(driver, tab):
    driver.switch_to.window(driver.window_handles[tab])
    driver.get(
        "https://www.betfair.com/exchange/plus/horse-racing/",
    )

    WebDriverWait(driver, 60).until(
        EC.element_to_be_clickable((By.XPATH, '//*[@id="onetrust-accept-btn-handler"]'))
    ).click()
    driver.switch_to.default_content()


def get_betfair_page(driver, market_id, tab):
    driver.switch_to.window(driver.window_handles[tab])
    driver.get(
        "https://www.betfair.com/exchange/plus/horse-racing/market/%s" % str(market_id),
    )
    WebDriverWait(driver, 30).until(
        EC.visibility_of_element_located,
        (
            (
                By.XPATH,
                '//*[@id="main-wrapper"]/div/div[2]/div/ui-view/div/div/div[1]/div[3]/div/div[1]/div/bf-main-market/bf-main-marketview/div/div[2]/bf-marketview-runners-list[2]/div/div/div/table/tbody/tr[1]/td[4]/button/div/span[1]',
            )
        ),
    )


def scrape_odds_betfair(driver, tab):
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
        for i in range(3):
            try:
                back_odd_button = back_odds_buttons[i]
                back_odds = float(
                    back_odd_button.find("span", class_="bet-button-price").text
                )
                back_availiable = float(
                    back_odd_button.find("span", class_="bet-button-size").text.replace(
                        "£", ""
                    )
                )
                horses[name]["back_odds_%s" % str(i + 1)] = back_odds
                horses[name]["back_avaliable_%s" % str(i + 1)] = back_availiable
            except IndexError:
                pass

            try:
                lay_odd_button = lay_odds_buttons[i]
                lay_odds = float(
                    lay_odd_button.find("span", class_="bet-button-price").text
                )
                lay_avaliable = float(
                    lay_odd_button.find("span", class_="bet-button-size").text.replace(
                        "£", ""
                    )
                )
                horses[name]["lay_odds_%s" % str(i + 1)] = lay_odds
                horses[name]["lay_avaliable_%s" % str(i + 1)] = lay_avaliable
            except IndexError:
                pass
    return horses
