import requests
import datetime
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np

from .betfair import login_betfair, get_event, get_horses


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
                        bookies[bookie] = {"min_runners": min_runners}
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
    race_df = pd.DataFrame(
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
    # for bookie in race["bookies"]:
    #     bookie_data = [
    #         race["venue"],
    #         time,
    #         bookie,
    #         race["place_payout"],
    #         race["places_paid"],
    #         race["bookies"][bookie]["min_runners"],
    #         event_id,
    #         win_market_id,
    #         place_market_id,
    #     ]
    #     data.append(bookie_data)

    # race_df = pd.DataFrame(
    #     data,
    #     columns=[
    #         "venue",
    #         "time",
    #         "bookie",
    #         "place_payout",
    #         "places_paid",
    #         "min_runners",
    #         "event_id",
    #         "win_market_id",
    #         "place_market_id",
    #     ],
    # )

    # race_df = pd.pivot(
    #     race_df,
    #     values=["place_payout", "places_paid", "min_runners", "event_id"],
    #     index=["venue", "time"],
    #     columns="bookie",
    # )
    # race_df = race_df.swaplevel(axis=1)
    # race_df.sort_index(level=0, axis=1, inplace=True)

    return race_df


def create_odds_df(race_df, races):
    odds = {}
    for race in race_df.iterrows():
        horses = []
        horse_ids = []
        key = race[0]
        for horse in get_horses(race[1].event_id, key[1], headers)[1]["runners"]:
            horses.append(horse["runnerName"])
            horse_ids.append(horse["selectionId"])
        races_key = race[1]["races_index"]
        indexes = races[races_key]["bookies"]
        data = [
            "back_odds",
            "lay_odds",
            "back_liability",
            "lay_liability",
            "horse_id",
        ]
        columns = pd.MultiIndex.from_product([horses, data], names=["horses", "data"])
        df = pd.DataFrame(index=indexes, columns=columns)
        print(df.xs("horse_id", level=1, drop_level=False, axis=1))
        odds[key] = df
    return odds


headers = login_betfair()


def run_extra_place():
    races = get_extra_place_races()
    race_df = create_race_df(races)
    odds = create_odds_df(race_df, races)
