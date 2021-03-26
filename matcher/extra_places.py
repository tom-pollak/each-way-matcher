import datetime
import pandas as pd
import numpy as np
from .run import setup_selenium
from .scrape_races import generate_df
from .betfair_scrape import setup_betfair_scrape, get_site, scrape_odds
from .william_hill import get_william_hill_page

def update_odds_df(odds_df, horses):
    idx = pd.IndexSlice
    for horse in horses:
        try:
            for data in horses[horse]:
                data_loc = odds_df.loc[idx[:, :, horse], idx['Betfair Exchange', data]]
                if data_loc.isnull().values.any():
                    odds_df.loc[idx[:, :, horse], idx['Betfair Exchange', data]] = np.array([horses[horse][data]])
                else:
                    print(odds_df.loc[idx[:, :, horse], idx['Betfair Exchange', data]])
                    odds_df.loc[idx[:, :, horse], idx['Betfair Exchange', data]] = np.append(odds_df.loc[idx[:, :, horse], idx['Betfair Exchange', data]], [horses[horse][data]])
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
        update_odds_df(odds_df, horses)
        get_site(driver, race.place_market_id, tab=0)
        horses = scrape_odds(driver, 0)
        odds_df = update_odds_df(odds_df, horses)
        break

    print(odds_df.iloc[0])

    #time = datetime.datetime(2021, 3, 25, 23, 26)
    #get_william_hill_page(driver, "Sam Houston", time, 0)
