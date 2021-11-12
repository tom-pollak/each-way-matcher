import requests
import datetime
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import matcher.sites.william_hill as william_hill

from matcher.exceptions import MatcherError
import matcher.sites.betfair as betfair

enabled_sites = {"William Hill": william_hill}


def get_extra_place_races():
    def make_date(added_days):
        dt = datetime.datetime.now() + datetime.timedelta(days=added_days)
        if 4 <= dt.day <= 20 or 24 <= dt.day <= 30:
            suffix = "th"
        else:
            suffix = ["st", "nd", "rd"][dt.day % 10 - 1]
        return f"({dt:%A} {dt.day}{suffix} {dt:%B} {dt.year})"

    headers = {
        "User-Agent": "Mozilla/5.0 (X11; CrOS x86_64 8172.45.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.64 Safari/537.36"
    }
    extra_places_page = requests.get(
        "https://matchedbettingblog.com/extra-place-offers-today/", headers=headers
    )

    soup = BeautifulSoup(extra_places_page.text, "html.parser")
    content = soup.find(class_="mbb-offer-list__extra-places")
    races = {}
    for tag in content:
        if tag.name == "h2":
            if tag.text == make_date(0):
                pass
            elif tag.text == make_date(1):
                break
            else:
                race_time, venue = tuple(tag.text.split(" ", 1))
                hour, mins = race_time.split(":")
                time = datetime.datetime.combine(
                    datetime.date.today(), datetime.time(int(hour), int(mins))
                )
                key = (venue, time)
                race = {}

        elif (
            tag.name == "div"
            and tag["class"][0] == "mbb-offer-list__extra-places__places"
        ):
            places_paid, place_payout = tuple(
                tag.text.replace("(", "").replace(")", "").split(", ")
            )
            places_paid = places_paid.split()[0]
            place_payout = int(place_payout.split()[0][0]) / int(
                place_payout.split()[0][2]
            )
            race["places_paid"] = places_paid
            race["place_payout"] = place_payout
        else:
            bookies = {}
            for bookie_tag in tag.contents:
                try:
                    bookie, min_runners = tuple(bookie_tag.text.split(" ("))
                    min_runners = int(min_runners.replace(")", "").replace("+", ""))
                except ValueError:
                    bookie = bookie_tag.text
                    min_runners = 0
                bookies[bookie] = min_runners
            race["bookies"] = bookies
            races[key] = race
    return races


def create_race_df(races):
    data = []
    indexes = []
    for (venue, time), race in races.items():
        if time > datetime.datetime.now():
            try:
                market_ids = betfair.get_market_id(venue, time)
                win_market_id = market_ids["win"]
                place_market_id = market_ids["place"]
            except MatcherError:
                print("matcher error")
                continue
            indexes.append((venue, time))
            data.append(
                [
                    win_market_id,
                    place_market_id,
                    race["place_payout"],
                    race["places_paid"],
                ]
            )
    indexes = pd.MultiIndex.from_tuples(indexes, names=("venue", "time"))
    races_df = pd.DataFrame(
        data,
        columns=[
            "win_market_id",
            "place_market_id",
            "place_payout",
            "places_paid",
        ],
        index=indexes,
    )
    races_df.sort_index(level=0, inplace=True)
    return races_df


def create_odds_df(races_df, races):
    bookies = set()
    for i in [
        [bookie for bookie in x["bookies"].keys() if bookie in enabled_sites]
        for x in races.values()
    ]:
        bookies.update(i)
    indexes = []
    data = []

    for race in races_df.iterrows():
        venue, time = race[0]
        try:
            horses = betfair.get_horses(venue, time)
            for horse_name, selection_id in horses.items():
                index = (venue, time, horse_name)
                indexes.append(index)
                data.append(
                    [
                        np.NaN,
                        np.NaN,
                        str(selection_id),
                        np.NaN,
                        np.NaN,
                        np.NaN,
                        str(selection_id),
                        np.NaN,
                    ]
                )
        except MatcherError:
            continue

    indexes = pd.MultiIndex.from_tuples(indexes, names=["venue", "time", "horse"])
    columns = pd.MultiIndex.from_product(
        [bookies, ["odds", "ep_ev"]], names=["bookies", "data"]
    )
    odds_df = pd.DataFrame(index=indexes, columns=columns)
    df_betfair = pd.DataFrame(
        data,
        columns=pd.MultiIndex.from_product(
            [
                ["Betfair Exchange Win", "Betfair Exchange Place"],
                ["odds", "available", "selection_id", "r_prob"],
            ],
        ),
        index=odds_df.index,
    )
    odds_df = odds_df.join(df_betfair)
    odds_df.sort_index(inplace=True)
    # odds_df.columns = odds_df.sort_index(axis=1).columns
    return odds_df


def create_bookies_df(races_df, races):
    idx = pd.IndexSlice
    try:
        indexes = pd.MultiIndex.from_tuples(races_df.index.values)
    except TypeError:
        return None
    # bookies = set(odds_df.columns.get_level_values("bookies"))
    bookies = list(enabled_sites.keys())
    columns = pd.MultiIndex.from_product(
        [bookies, ["min_runners", "tab_id"]], names=("bookies", "data")
    )
    bookies_df = pd.DataFrame(index=indexes, columns=columns)

    for index in indexes:
        min_runners = races[index]["bookies"]
        min_runners_index = pd.MultiIndex.from_product(
            [min_runners.keys(), ["min_runners"]], names=["bookies", "data"]
        )
        min_runners = pd.Series(min_runners.values(), index=min_runners_index)
        bookies_df.loc[index, idx[:, "min_runners"]] = min_runners
    return bookies_df


def generate_df():
    races = get_extra_place_races()
    races_df = create_race_df(races)
    odds_df = create_odds_df(races_df, races)
    bookies_df = create_bookies_df(races_df, odds_df, races)
    return races_df, odds_df, bookies_df
