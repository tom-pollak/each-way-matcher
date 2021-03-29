import datetime
import pandas as pd
from .run import setup_selenium
from .scrape_races import generate_df
from .scrape_betfair import setup_scrape_betfair, get_site, scrape_odds_betfair
from .william_hill import get_william_hill_page, scrape_odds_william_hill


idx = pd.IndexSlice
enabled_sites = {
    "William Hill": {"get": get_william_hill_page, "scrape": scrape_odds_william_hill}
}


def update_odds_df(odds_df, horses, bookie):
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


def get_tab_id(bookies_df, venue, time, site):
    return bookies_df.at[(venue, time), (site, "tab_id")]


def create_tab_id(driver, bookies_df, venue, time, site, tab):
    driver.execute_script("""window.open("https://google.com","_blank");""")
    driver.switch_to.window(driver.window_handles[tab])
    bookies_df.at[(venue, time), (site, "tab_id")] = tab
    tab += 1
    return tab


def get_odds(driver, odds_df, bookies_df):
    for tab in range(max(bookies_df.loc[:, idx[:, "tab_id"]])):
        row = bookies_df.at[:, idx[:, tab]]
        print(row)
        if row:
            site = row.columns.get_level_values("bookies")
            race = row.index
            print(site, race)
            horses = sites[site]["scrape"](driver, tab)
            update_odds_df(odds_df, horses, site)


def close_races(driver, races_df, bookies_df):
    pass


def run_extra_places():
    tab = 0
    races_df, odds_df, bookies_df, horse_id_df = generate_df()
    driver = setup_selenium()
    setup_scrape_betfair(driver, tab=0)
    for index, race in (
        races_df.sort_values("time", ascending=True).sort_index(level=1).iterrows()
    ):
        sites = [site for site in enabled_sites if site in horse_id_df[index].columns]
        if sites:
            tab = create_tab_id(
                driver, bookies_df, index[0], index[1], "Betfair Exchange Win", tab
            )
            get_site(driver, race.win_market_id, tab)
            horses = scrape_odds_betfair(driver, tab)
            update_odds_df(odds_df, horses, "Betfair Exchange Win")

            tab = create_tab_id(
                driver, bookies_df, index[0], index[1], "Betfair Exchange Place", tab
            )
            get_site(driver, race.place_market_id, tab)
            horses = scrape_odds_betfair(driver, tab)
            update_odds_df(odds_df, horses, "Betfair Exchange Place")

            for site in sites:
                tab = create_tab_id(driver, bookies_df, index[0], index[1], site, tab)
                sites[site]["get"](driver, index[0], index[1], tab)
                horses = sites[site]["scrape"](driver, tab)
                update_odds_df(odds_df, horses, site)
            break  # debug
