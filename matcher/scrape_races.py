import requests
import datetime
from bs4 import BeautifulSoup
import pandas as pd

from .betfair_api import login_betfair, get_event, get_horses


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
                # bookies["Betfair Exchange"] = 0
                race["bookies"] = bookies
    return races


def create_race_df(races):
    headers = login_betfair()
    data = []
    indexes = []
    for i, race in enumerate(races):
        hour, min = race["time"].split(":")
        time = datetime.datetime.combine(
            datetime.date.today(), datetime.time(int(hour), int(min))
        )
        event_id = get_event(race["venue"], time, headers)
        if not event_id:
            continue
        try:
            market_ids, _ = get_horses(event_id, time, headers)
            win_market_id = market_ids["Win"]
            place_market_id = market_ids["Place"]
        except ValueError:
            continue
        indexes.append((race["venue"], time))
        data.append(
            [
                event_id,
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
            "event_id",
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
    headers = login_betfair()
    horses = []
    horse_ids = {}
    bookies = set()
    for i in [x["bookies"].keys() for x in races]:
        bookies.update(i)
    indexes = []

    data = [
        "back_odds",
        "horse_id",
    ]

    for race in races_df.iterrows():
        key = race[0]
        for horse in get_horses(race[1].event_id, key[1], headers)[1]["runners"]:
            indexes.append((key[0], key[1], horse["runnerName"]))
            horse_ids[horse["runnerName"]] = horse["selectionId"]

    indexes = pd.MultiIndex.from_tuples(indexes, names=["venue", "time", "horse"])
    columns = pd.MultiIndex.from_product([bookies, data], names=["bookies", "data"])
    df = pd.DataFrame(index=indexes, columns=columns)
    df_betfair = pd.DataFrame(
        columns=pd.MultiIndex.from_product(
            [
                ["Betfair Exchange Win", "Betfair Exchange Place"],
                [
                    "horse_id",
                    "back_odds_1",
                    "back_odds_2",
                    "back_odds_3",
                    "lay_odds_1",
                    "lay_odds_2",
                    "lay_odds_3",
                    "back_avaliable_1",
                    "back_avaliable_2",
                    "back_avaliable_3",
                    "lay_avaliable_1",
                    "lay_avaliable_2",
                    "lay_avaliable_3",
                ],
            ],
        ),
        index=df.index,
    )
    df = df.join(df_betfair)
    idx = pd.IndexSlice
    for i, _ in df.xs("horse_id", level=1, drop_level=False, axis=1).iterrows():
        df.loc[i, idx[:, "horse_id"]] = horse_ids[i[2]]
    return df


def create_min_runners_df(races_df, odds_df, races):
    try:
        indexes = pd.MultiIndex.from_tuples(races_df.index.values)
    except TypeError:
        return None
    bookies = set(odds_df.columns.get_level_values("bookies"))
    min_runners_df = pd.DataFrame(index=indexes, columns=bookies)

    for index in indexes:
        bookies = races[races_df.loc[index].races_index]["bookies"]
        min_runners_df.loc[index] = pd.Series(bookies)
    races_df.drop(columns=["races_index"], inplace=True)
    return min_runners_df


def generate_df():
    races = get_extra_place_races()
    races_df = create_race_df(races)
    odds_df = create_odds_df(races_df, races)
    min_runners_df = create_min_runners_df(races_df, odds_df, races)
    return races_df, odds_df, min_runners_df
