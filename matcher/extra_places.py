import pandas as pd

import matcher.sites.betfair as betfair
import matcher.sites.william_hill as william_hill
from matcher.setup import setup_selenium
from matcher.exceptions import MatcherError
from matcher.sites.scrape_extra_places import generate_df
from selenium.common.exceptions import WebDriverException

from matcher.calc_places_prob import (
    calc_horse_place_probs,
    get_ev_ep_races,
)
from matcher.calculate import minimize_loss, calculate_profit


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
    for index, _ in (
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
                try:
                    enabled_sites[site].get_page(driver, index[0], index[1], tab)
                except WebDriverException:
                    print(f"couldn't get site: {index}")
                    continue

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
            try:
                horses = enabled_sites[site].scrape(driver, i)
            except (WebDriverException, IndexError):
                print("couldn't get", venue, time)
                continue
            update_odds_df(odds_df, venue, time, horses, site)


def get_betfair_odds(races_df, odds_df):
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


def update_r_probs(odds_df):
    for race, odds in odds_df.groupby(level=["venue", "time"]):
        data = (
            odds_df.loc[idx[race], idx["Betfair Exchange Win"]]["odds"]
            .dropna()
            .to_dict()
        )
        r_prob = calc_horse_place_probs(data)
        r_prob = {race + (k,): v for k, v in r_prob.items()}
        for k, v in r_prob.items():
            odds_df[idx["Betfair Exchange Win", "r_prob"]] = odds_df[
                idx["Betfair Exchange Win", "r_prob"]
            ].astype("object")
            odds_df.at[k, idx["Betfair Exchange Win", "r_prob"]] = v


def update_ep_ev(odds_df, race, odds):
    place_payout = 5
    win_available = place_available = betfair_balance = 1000

    bookie_odds = odds.loc["William Hill", "odds"]
    win_odds = odds.loc["Betfair Exchange Win", "odds"]
    place_odds = odds.loc["Betfair Exchange Place", "odds"]
    r_prob = odds.loc["Betfair Exchange Win", "r_prob"]
    win_prob = r_prob[0]
    place_prob = sum(r_prob[:3])
    lose_prob = sum(r_prob[4:])
    ep_prob = r_prob[3]
    bookie_stake = 10
    profits = calculate_profit(
        bookie_odds,
        bookie_stake,
        win_odds,
        0,
        place_odds,
        0,
        place_payout,
    )
    win_stake, place_stake = minimize_loss(
        win_odds,
        place_odds,
        win_available,
        place_available,
        profits,
        betfair_balance,
        place_payout,
    )

    ev = get_ev_ep_races(
        bookie_odds,
        win_odds,
        place_odds,
        win_prob,
        place_prob,
        lose_prob,
        ep_prob,
    )
    odds_df.at[race, [["William Hill", "ep_ev"]]] = ev


def find_pos_ev_runners(odds_df):
    pos_ev_r = odds_df.loc[:, idx[:, "ep_ev"]]
    pos_ev_r.columns = pos_ev_r.columns.droplevel(1)

    for site in enabled_sites:
        pos_ev_r = pos_ev_r[pos_ev_r[site] > 0]

    if pos_ev_r.empty:
        return None
    return pos_ev_r


# def run_extra_places():
#     odds_df = pd.read_pickle("odds_df")
#     races_df = pd.read_pickle("races_df")
#     bookies_df = pd.read_pickle("bookies_df")


def run_extra_places():
    races_df, odds_df, bookies_df = generate_df()
    driver = setup_selenium()
    tab = setup_sites(driver, races_df, bookies_df)
    while True:
        get_bookie_odds(driver, odds_df, bookies_df, tab)
        get_betfair_odds(races_df, odds_df)
        # odds_df.dropna(how="all", inplace=True).dropna(how="all", axis=1, inplace=True)

        update_r_probs(odds_df)
        for race, odds in odds_df.iterrows():
            update_ep_ev(odds_df, race, odds)  # not finished!

        pos_ev_r = find_pos_ev_runners(odds_df)
        if pos_ev_r is None:
            print("No +ev horse found")
        else:
            print("horses found!")
            print(pos_ev_r)

        odds_df.to_pickle("odds_df")
        races_df.to_pickle("races_df")
        bookies_df.to_pickle("bookies_df")
        driver.quit()
        return
