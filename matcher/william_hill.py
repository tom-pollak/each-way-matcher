import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def get_page(driver, venue, time):
    driver.switch_to.window(driver.window_handles[tab])
    driver.get(
        "https://sports.williamhill.com/betting/en-gb/horse-racing/meetings/all/today"
    )
    WebDriverWait(driver, 60).until(
        EC.visibility_of_element_located(
            (
                By.XPATH,
                '//*[@id="header-root"]/div/div/div/div[1]/div/div/div[1]/a/span/svg',
            )
        )
    )
    venues = driver.find_elements_by_class_name("component-race-row")
    for race_venue in venues:
        print(venue.find_element_by_class_name("race-row-header"))
        if race_venue.find_element_by_class_name("title").text == venue:
            for race_time_button in race_venue.find_elements_by_class_name(
                "non-route component-race-button"
            ):
                if race_time_button.text == time.strftime("%H:%M"):
                    race_time_button.click()


time = datetime.datetime(2021, 3, 25, 21, 28)
get_page("Golden Gate", time)
