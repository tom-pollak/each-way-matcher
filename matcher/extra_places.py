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
                data_loc = odds_df.loc[
                    idx[:, :, horse], idx["Betfair Exchange %s" % win_place, data]
                ]
                if data_loc.isnull().values.any():
                    data_loc = np.array([horses[horse][data]])
                else:
                    print(data_loc)
                    data_loc = np.append(
                        data_loc,
                        [horses[horse][data]],
                    )
        except KeyError:
            continue
    return odds_df


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
        # odds_df = update_odds_df(odds_df, horses, "Place")
        break

    first_horse = odds_df.loc[idx[:, :, horses[0]], idx["Betfair Exchange Win", data]]
    print(first_horse)

    # time = datetime.datetime(2021, 3, 25, 23, 26)
    # get_william_hill_page(driver, "Sam Houston", time, 0)
