from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import StaleElementReferenceException


def get_william_hill_page(driver, venue, time, tab):
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
            print("found venue")
            for race_time_button in race_venue.find_elements_by_class_name(
                "component-race-button"
            ):
                try:
                    if race_time_button.text == time.strftime("%H:%M"):
                        race_time_button.click()
                except StaleElementReferenceException:
                    pass


def scrape_odds_william_hill(driver, tab):
    driver.switch_to.window(driver.window_handles[tab])
    table = WebDriverWait(driver, 60).until(
        EC.visibility_of_element_located(
            (
                By.XPATH,
                '//*[@id="racing-meetings"]/div/div/div[3]/div[6]/div[2]/div[2]/div[2]/table/tbody',
            )
        )
    )
    rows = table.find_elements_by_css_selector("tr[role='row']")
    print(rows)
