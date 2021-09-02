from bs4 import BeautifulSoup

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def login(driver):
    raise NotImplementedError




def get_balance(driver):
    raise NotImplementedError




def click_betslip(driver):
    raise NotImplementedError




def click_horse(driver, horse_name):
    raise NotImplementedError




def close_bet(driver):
    raise NotImplementedError




def click_horse(driver):
    raise NotImplementedError




def get_page(driver, venue, time, tab):
    driver.switch_to.window(driver.window_handles[tab])
    driver.get(
        "https://sports.williamhill.com/betting/en-gb/horse-racing/meetings/all/today"
    )
    WebDriverWait(driver, 60).until(
        EC.visibility_of_element_located(
            (
                By.XPATH,
                '//*[@id="meetings-app"]/div[5]',
            )
        )
    )
    venues = driver.find_elements_by_class_name("component-race-row")
    for race_venue in venues:
        race_venue_name = race_venue.find_element_by_class_name("title").text.split(
            " ("
        )[0]
        if race_venue_name == venue:
            for race_time_button in race_venue.find_elements_by_class_name(
                "component-race-button"
            ):
                if race_time_button.text == time.strftime("%H:%M"):
                    race_time_button.click()
                    WebDriverWait(driver, 60).until(
                        EC.visibility_of_element_located(
                            (By.CSS_SELECTOR, 'tbody[role="rowgroup"]')
                        )
                    )
                    return


def scrape(driver, tab):
    driver.switch_to.window(driver.window_handles[tab])
    horses = {}
    soup = BeautifulSoup(driver.page_source, "html.parser")
    table = soup.select("tbody[role='rowgroup']")[0]
    rows = table.select("tr[role='row']")
    for row in rows:
        name = row.find("span", class_="selection__title").text
        odds = row.find("button", class_="sp-betbutton").text.split("/")
        if odds[0] == "SP":
            continue
        if odds[0] == "EVS":
            odds = 1
        else:
            odds = float(odds[0]) / float(odds[1]) + 1
        if "- N/R" not in name:
            horses[name] = odds
    return horses
