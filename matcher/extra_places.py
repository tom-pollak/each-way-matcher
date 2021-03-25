from .run import setup_selenium
from .scrape_races import generate_df
from .betfair_scrape import get_site, scrape_odds


def run_extra_places():
    races_df, odds_df, min_runners_df = generate_df()
    driver = setup_selenium()
    get_site(driver, races_df.iloc[0].market_id)
    horses = scrape_odds(driver, 0)
    print(horses)
