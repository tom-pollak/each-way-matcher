import datetime
import pandas as pd
import numpy as np
from .run import setup_selenium
from .scrape_races import generate_df
from .betfair_scrape import setup_betfair_scrape, get_site, scrape_odds
from .william_hill import get_william_hill_page


def update_odds_df(odds_df, horses, win_place):
    idx = pd.IndexSlice
    for horse in horses:
        try:
            for data in horses[horse]:
                mask = [idx[:, :, horse], idx["Betfair Exchange %s" % win_place, data]]
                series_data = pd.Series([[]])
                if odds_df.loc[mask[0], mask[1]].isnull().values.any():
                    odds_df.at[mask[0], mask[1]] = [1, 2, 3]
                else:
                    odds_df.at[mask[0], mask[1]].append(series_data)
                print(odds_df.loc[mask[0], mask[1]])
        except KeyError:
            continue


def run_extra_places():
    races_df, odds_df, min_runners_df = generate_df()
    driver = setup_selenium()
    setup_betfair_scrape(driver, tab=0)
    for (venue, time), race in races_df.iterrows():
        get_site(driver, race.win_market_id, tab=0)
        horses = scrape_odds(driver, 0)
        update_odds_df(odds_df, horses, "Win")
        # get_site(driver, race.place_market_id, tab=0)
        # horses = scrape_odds(driver, 0)
        # update_odds_df(odds_df, horses, "Place")
        break
    idx = pd.IndexSlice
    first_horse = odds_df.loc[
        idx[:, :, "Never Mistabeat"], idx["Betfair Exchange Win", :]
    ]
    print(first_horse)

    # time = datetime.datetime(2021, 3, 25, 23, 26)
    # get_william_hill_page(driver, "Sam Houston", time, 0)
