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
    # print(res)
    raise MatcherError


def get_position(venue, time, horse_name):
    try:
        race_id = get_race_id(venue, time)
        res = call_api("https://horse-racing.p.rapidapi.com/race/%s" % race_id)
    except MatcherError:
        return None

    for horse in res["horses"]:
        if horse_name in horse["horse"]:
            if horse["non_runner"] == "1":
                return "Non-runner"
            try:
                return float(horse["position"])
            except ValueError:
                print(horse)

    # print(res["horses"])
    return None
