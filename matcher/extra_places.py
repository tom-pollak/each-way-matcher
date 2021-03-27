import datetime
import pandas as pd
import numpy as np
from .run import setup_selenium
from .scrape_races import generate_df
from .betfair_scrape import setup_betfair_scrape, get_site, scrape_odds
from .william_hill import get_william_hill_page


def update_odds_df(odds_df, horses, win_place):
    idx = pd.IndexSlice
    current_time = datetime.datetime.now()
    for horse in horses:
        try:
            data = horses[horse]
            values = list(horses[horse].values())
            mask = [
                idx[:, :, horse, current_time],
                idx["Betfair Exchange %s" % win_place, data],
            ]
            odds_df.loc[mask[0], mask[1]] = values
            print(odds_df.loc[mask[0], mask[1]])
        except KeyError:
            continue


def run_extra_places():
    races_df, odds_df, min_runners_df, horse_id_df = generate_df()
    driver = setup_selenium()
    setup_betfair_scrape(driver, tab=0)
    for (venue, time), race in races_df.iterrows():
        get_site(driver, race.win_market_id, tab=0)
        horses = scrape_odds(driver, 0)
        update_odds_df(odds_df, horses, "Win")
        # get_site(driver, race.place_market_id, tab=0)
        # horses = scrape_odds(driver, 0)
        # update_odds_df(odds_df, horses, "Place")
        # break
