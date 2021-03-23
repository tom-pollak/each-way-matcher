import requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import pandas as pd


def get_extra_place_races():
    def make_date(added_days):
        dt = datetime.now() + timedelta(days=added_days)
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
                        bookies[bookie] = {"min_runners": min_runners, "odds": []}
                race["bookies"] = bookies
    return races


def create_dataframe(races):
    index_tuples = []
    bookies_tuples = []
    for race in races:
        index_tuples.append(race["venue"], race["time"])
    index = pd.MultiIndex.from_tuples(tuples, names=["venue", "time"])


races = get_extra_place_races()
create_dataframe(races)
