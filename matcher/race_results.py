import os
import requests
from datetime import datetime
from dotenv import load_dotenv

from .exceptions import MatcherError

BASEDIR = os.path.abspath(os.path.dirname(__file__) + "/../")
load_dotenv(os.path.join(BASEDIR, ".env"))
RAPID_API_KEY = os.environ.get("RAPID_API_KEY")


def call_api(url, params=None):
    headers = {
        "x-rapidapi-host'": "horse-racing.p.rapidapi.com",
        "x-rapidapi-key": RAPID_API_KEY,
    }
    res = requests.request("GET", url, headers=headers, params=params)
    if res.status_code == 200:
        return res.json()
    print(res.text)
    raise MatcherError


def get_race_id(venue, time):
    params = {"date": str(time)}
    res = call_api("https://horse-racing.p.rapidapi.com/results", params=params)
    for race in res:
        race_time = datetime.strptime(race["date"], "%Y-%m-%d %H:%M:%S")
        if (venue in race["course"] or race["course"] in venue) and time == race_time:
            return race["id_race"]

    races = []
    for race in res:
        races.append((race["course"], race["date"]))
    raise MatcherError(races)


def get_position(venue, time, horse_name):
    try:
        race_id = get_race_id(venue, time)
    except MatcherError as venues:
        print("Course not found: %s, %s\n%s" % (venue, time, venues))
        return None

    try:
        res = call_api("https://horse-racing.p.rapidapi.com/race/%s" % race_id)
    except MatcherError:
        return "Rate limit exceeded"

    for horse in res["horses"]:
        if horse_name in horse["horse"]:
            if horse["non_runner"] == "1" or horse["position"] == "pu":
                return 999
            return float(horse["position"])
    return None
