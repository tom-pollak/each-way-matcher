import pandas as pd
import numpy as np
from datetime import datetime

import matcher.sites.betfair as betfair
import matcher.sites.william_hill as william_hill
from matcher.setup import setup_selenium
from matcher.exceptions import MatcherError
from matcher.sites.scrape_extra_places import generate_df


idx = pd.IndexSlice
enabled_sites = {"William Hill": william_hill}


def update_odds_df(odds_df, venue, time, horses, bookie):
    for horse, odd in horses.items():
        if isinstance(odd, tuple):
            odd, available = odd
            odds_df.loc[idx[venue, time, horse], idx[bookie, "available"]] = available
        odds_df.loc[idx[venue, time, horse], idx[bookie, "odds"]] = odd


def setup_sites(driver, races_df, bookies_df):
    tab = 0
    for index, race in (
        races_df.query("time > @datetime.now()")
        .sort_values("time", ascending=True)
        .sort_index(level=1)
        .iterrows()
    ):
        sites = [
            site
            for site in enabled_sites
            if site in bookies_df.loc[index].index.get_level_values("bookies")
        ]
        if sites:
            for site in sites:
                tab = create_tab_id(driver, bookies_df, index[0], index[1], site, tab)
                enabled_sites[site].get_page(driver, index[0], index[1], tab)

    driver.switch_to.window(driver.window_handles[0])
    driver.close()
    return tab


def create_tab_id(driver, bookies_df, venue, time, site, tab):
    driver.execute_script("""window.open("https://google.com","_blank");""")
    driver.switch_to.window(driver.window_handles[tab])
    bookies_df.at[(venue, time), (site, "tab_id")] = tab
    tab += 1
    return tab


def get_bookie_odds(driver, odds_df, bookies_df, tab):
    for i in range(tab):
        tabs = bookies_df.loc[:, idx[:, "tab_id"]]
        row = tabs.where(tabs == i).dropna(how="all").dropna(how="all", axis=1)
        site = row.columns.get_level_values("bookies")[0]
        venue, time = row.index[0]
        if site in enabled_sites:
            horses = enabled_sites[site].scrape(driver, i)
            update_odds_df(odds_df, venue, time, horses, site)


def get_betair_odds(races_df, odds_df):
    for index, race in (
        races_df.query("time > @datetime.now()")
        .sort_values("time", ascending=True)
        .sort_index(level=1)
        .iterrows()
    ):
        horses_win = {}
        horses_place = {}
        for name, selection_id in odds_df.loc[index, "Betfair Exchange Win"][
            "selection_id"
        ].items():
            try:
                horses_win[name] = betfair.get_odds(race["win_market_id"], selection_id)
                horses_place[name] = betfair.get_odds(
                    race["place_market_id"], selection_id
                )
            except (MatcherError, ValueError):
                odds_df.drop((index[0], index[1], name), inplace=True)
                continue
        update_odds_df(odds_df, index[0], index[1], horses_win, "Betfair Exchange Win")
        update_odds_df(
            odds_df, index[0], index[1], horses_place, "Betfair Exchange Place"
        )


def close_races(driver, races_df, bookies_df):
    pass


def run_extra_places():
    races_df, odds_df, bookies_df = generate_df()
    print(races_df, odds_df, bookies_df)
    driver = setup_selenium()
    tab = setup_sites(driver, races_df, bookies_df)
    odds_df.sort_index(0, inplace=True)
    while True:
        get_bookie_odds(driver, odds_df, bookies_df, tab)
        get_betair_odds(races_df, odds_df)

        # debug
        odds_df.sort_index(0, inplace=True)
        print(races_df)
        print(odds_df.dropna(how="all").dropna(how="all", axis=1).to_string())
        driver.quit()
        return
