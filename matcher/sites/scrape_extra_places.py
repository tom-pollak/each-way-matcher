import requests
import datetime
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np

from matcher.exceptions import MatcherError
import matcher.sites.betfair as betfair


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
    content = soup.find("article").find_all(class_="has-text-align-center")[1:-1]
    races = []
    race = None
    for tag in content:
        if tag.name == "h2":
            if race is not None:
                races.append(race)
            if tag.text == make_date(0):
                pass
            elif tag.text == make_date(1):
                break
            else:
                race_time, venue = tuple(tag.text.split())
                race = {"time": race_time, "venue": venue}

        elif tag.name == "p":
            if len(race) == 2:
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
                    if isinstance(bookie_tag, str):
                        try:
                            bookie, min_runners = tuple(bookie_tag.split(" ("))
                            min_runners = int(
                                min_runners.replace(")", "").replace("+", "")
                            )
                        except ValueError:
                            bookie = bookie_tag
                            min_runners = 0
                        bookies[bookie] = min_runners
                race["bookies"] = bookies
    return races


def create_race_df(races):
    data = []
    indexes = []
    for i, race in enumerate(races):
        hour, mins = race["time"].split(":")
        time = datetime.datetime.combine(
            datetime.date.today(), datetime.time(int(hour), int(mins))
        )
        try:
            market_ids = betfair.get_market_id(race["venue"], time)
            win_market_id = market_ids["win"]
            place_market_id = market_ids["place"]
        except:  # debug
            continue
        # except MatcherError:
        #     continue
        indexes.append((race["venue"], time))
        data.append(
            [
                win_market_id,
                place_market_id,
                race["place_payout"],
                race["places_paid"],
                i,
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
            "races_index",
        ],
        index=indexes,
    )
    races_df.sort_index(level=0, inplace=True)
    return races_df


def create_odds_df(races_df, races):
    bookies = set()
    for i in [x["bookies"].keys() for x in races]:
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
                    [np.NaN, np.NaN, selection_id, np.NaN, np.NaN, selection_id]
                )
        except MatcherError:
            continue

    indexes = pd.MultiIndex.from_tuples(indexes, names=["venue", "time", "horse"])
    columns = pd.MultiIndex.from_product(
        [bookies, ["back_odds"]], names=["bookies", "data"]
    )
    odds_df = pd.DataFrame(index=indexes, columns=columns)
    df_betfair = pd.DataFrame(
        data,
        columns=pd.MultiIndex.from_product(
            [
                ["Betfair Exchange Win", "Betfair Exchange Place"],
                [
                    # "back_odds_1",
                    # "back_odds_2",
                    # "back_odds_3",
                    "odds",
                    # "lay_odds_2",
                    # "lay_odds_3",
                    # "back_available_1",
                    # "back_available_2",
                    # "back_available_3",
                    "available",
                    # "lay_available_2",
                    # "lay_available_3",
                    "selection_id",
                ],
            ],
        ),
        index=odds_df.index,
    )
    odds_df = odds_df.join(df_betfair)
    odds_df.sort_index(inplace=True)
    return odds_df


def create_bookies_df(races_df, odds_df, races):
    idx = pd.IndexSlice
    try:
        indexes = pd.MultiIndex.from_tuples(races_df.index.values)
    except TypeError:
        return None
    bookies = set(odds_df.columns.get_level_values("bookies"))
    columns = pd.MultiIndex.from_product(
        [bookies, ["min_runners", "tab_id"]], names=("bookies", "data")
    )
    bookies_df = pd.DataFrame(index=indexes, columns=columns)

    for index in indexes:
        min_runners = races[races_df.loc[index].races_index]["bookies"]
        min_runners_index = pd.MultiIndex.from_product(
            [min_runners.keys(), ["min_runners"]], names=["bookies", "data"]
        )
        min_runners = pd.Series(min_runners.values(), index=min_runners_index)
        bookies_df.loc[index, idx[:, "min_runners"]] = min_runners
    races_df.drop(columns=["races_index"], inplace=True)
    return bookies_df


def generate_df():
    races = get_extra_place_races()
    races_df = create_race_df(races)
    odds_df = create_odds_df(races_df, races)
    bookies_df = create_bookies_df(races_df, odds_df, races)
    return races_df, odds_df, bookies_df
