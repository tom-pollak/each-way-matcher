import datetime
import pandas as pd
import numpy as np
from .run import setup_selenium
from .scrape_races import generate_df
from .betfair_scrape import setup_betfair_scrape, get_site, scrape_odds
from .william_hill import get_william_hill_page


def update_odds_df(odds_df, horses, bookie):
    idx = pd.IndexSlice
    current_time = datetime.datetime.now()
    for horse in horses:
        data = horses[horse]
        values_index = pd.MultiIndex.from_product(
            [[bookie], data.keys()], names=["bookies", "data"]
        )
        values = pd.Series(horses[horse].values(), index=values_index)
        try:
            venue, time, _, _ = odds_df.query("horse == @horse").index.values[0]
            odds_df.loc[
                idx[venue, time, horse, current_time], idx[bookie, data]
            ] = values
        except IndexError:
            pass
        try:
            odds_df.drop((venue, time, horse, pd.NaT), inplace=True)
        except KeyError:
            pass


def run_extra_places():
    # {'Global Esteem': {'back_odds_1': 9.0}}
    races_df, odds_df, bookies_df, horse_id_df = generate_df()
    driver = setup_selenium()
    setup_betfair_scrape(driver, tab=0)
    for (venue, time), race in races_df.iterrows():
        get_site(driver, race.win_market_id, tab=0)
        horses = scrape_odds(driver, tab=0)
        update_odds_df(odds_df, horses, "Betfair Exchange Win")
        break
        # get_site(driver, race.place_market_id, tab=0)
        # horses = scrape_odds(driver, 0)
        # update_odds_df(odds_df, horses, "Betfair Exchange Place")
