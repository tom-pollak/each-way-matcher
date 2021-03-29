from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


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
            for race_time_button in race_venue.find_elements_by_class_name(
                "component-race-button"
            ):
                if race_time_button.text == time.strftime("%H:%M"):
                    race_time_button.click()
                    return


def scrape_odds_william_hill(driver, tab):
    horses = {}
    driver.switch_to.window(driver.window_handles[tab])
    driver.refresh()
    table = WebDriverWait(driver, 60).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, 'tbody[role="rowgroup"]'))
    )
    rows = table.find_elements_by_css_selector("tr[role='row']")
    for row in rows:
        name = (
            WebDriverWait(row, 15)
            .until(
                EC.visibility_of_element_located((By.CLASS_NAME, "selection__title"))
            )
            .text
        )
        odds = (
            WebDriverWait(row, 15)
            .until(EC.visibility_of_element_located((By.CLASS_NAME, "sp-betbutton")))
            .text.split("/")
        )
        odds = float(odds[0]) / float(odds[1]) + 1
        if "- N/R" not in name:
            horses[name] = {"back_odds": odds}
    return horses
