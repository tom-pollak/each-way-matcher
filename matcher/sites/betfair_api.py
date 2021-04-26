import datetime
import json
import os
import difflib
import requests
import time

from urllib import error, request
from dotenv import load_dotenv

from matcher.exceptions import MatcherError
from matcher.calculate import round_stake

betting_url = "https://api.betfair.com/exchange/betting/json-rpc/v1"

venue_names = {"Cagnes-Sur-Mer": "Cagnes Sur Mer"}

BASEDIR = os.path.abspath(os.path.dirname(__file__) + "/../../")
load_dotenv(os.path.join(BASEDIR, ".env"))

APP_KEY = os.environ.get("APP_KEY")
USERNAME = os.environ.get("BETFAIR_USR")
PASSWORD = os.environ.get("BETFAIR_PASS")
CERT = os.path.join(BASEDIR, "client-2048.crt")
KEY = os.path.join(BASEDIR, "client-2048.key")

if None in (USERNAME, PASSWORD, APP_KEY):
    raise Exception("betfair env vars not set")


def login_betfair():
    payload = f"username={USERNAME}&password={PASSWORD}"
    login_headers = {
        "X-Application": APP_KEY,
        "Content-Type": "application/x-www-form-urlencoded",
    }
    try:
        response = requests.post(
            "https://identitysso-cert.betfair.com/api/certlogin",
            data=payload,
            cert=(CERT, KEY),
            headers=login_headers,
        )
    except requests.exceptions.ConnectionError as e:
        raise MatcherError("Can't login: %s" % e)

    if response.status_code == 200:
        SESS_TOK = response.json()["sessionToken"]
        return {
            "X-Application": APP_KEY,
            "X-Authentication": SESS_TOK,
            "content-type": "application/json",
        }

    raise MatcherError("Can't login")


def get_race_odds(market_id):
    horses = {}
    resp = requests.get(
        f"https://www.betfair.com/www/sports/exchange/readonly/v1/bymarket?_ak=nzIFcwyWhrlwYMrh&alt=json&currencyCode=GBP&locale=en_GB&marketIds={market_id}&rollupLimit=10&rollupModel=STAKE&types=EVENT,RUNNER_DESCRIPTION,%20RUNNER_EXCHANGE_PRICES_BEST"
    )
    horses_resp = resp.json()["eventTypes"][0]["eventNodes"][0]["marketNodes"][0][
        "runners"
    ]
    for horse in horses_resp:
        horse_name = horse["description"]["runnerName"]
        horses[horse_name] = {}
        back = horse["exchange"].get("availableToBack")
        lay = horse["exchange"].get("availableToLay")
        if back is None and lay is None:
            continue
        for i, odds in enumerate(back):
            horses[horse_name][f"back_odds_{i+1}"] = odds["price"]
            horses[horse_name][f"back_avaliable_{i+1}"] = odds["size"]
        for i, odds in enumerate(lay):
            horses[horse_name][f"lay_odds_{i+1}"] = odds["price"]
            horses[horse_name][f"lay_avaliable_{i+1}"] = odds["size"]
    return horses


def call_api(jsonrpc_req, headers, url=betting_url):
    try:
        if url.lower().startswith("http"):
            req = request.Request(url, jsonrpc_req.encode("utf-8"), headers)
        else:
            raise MatcherError("url does not start with http")
        with request.urlopen(req) as response:
            json_res = response.read()
            return json.loads(json_res.decode("utf-8"))
    except error.HTTPError:
        print("Not a valid operation" + str(url))
    except error.URLError:
        print("No service available at " + str(url))
    print(jsonrpc_req)
    raise MatcherError("API request failed")


def get_betfair_balance_in_bets():
    headers = login_betfair()
    balance_in_bets = 0
    order_req = '{"jsonrpc": "2.0", "method": "SportsAPING/v1.0/listCurrentOrders"}'
    res = call_api(order_req, headers)
    for race in res["result"]["currentOrders"]:
        odds = race["averagePriceMatched"]
        stake = race["sizeMatched"]
        stake_remaining = race["sizeRemaining"]
        original_odds = race["priceSize"]["price"]

        balance_in_bets += stake * (odds - 1) + stake_remaining * (original_odds - 1)
    return balance_in_bets


def get_horse_id(horses, target_horse):
    for horse in horses["runners"]:
        if horse["runnerName"].lower() == target_horse.lower():
            return horse["selectionId"], horse["runnerName"]

    # sometimes runnerName is 1. horse_name
    for horse in horses["runners"]:
        if target_horse.lower() in horse["runnerName"].lower():
            return (
                horse["selectionId"],
                target_horse,
            )  # as 1. is not the valid horse name

    # for horses with punctuation taken out by oddsmonkey
    horses_list = [horse["runnerName"] for horse in horses["runners"]]
    close_horse = difflib.get_close_matches(target_horse, horses_list, n=1)[0]
    print("Close horse found: %s" % close_horse)
    for horse in horses["runners"]:
        if horse["runnerName"] == close_horse:
            return horse["selectionId"], horse["runnerName"]

    print("ERROR couldn't find horse selection_id")
    return None, target_horse


def get_horses(venue, race_time, headers):
    markets = []
    markets_ids = {}
    markets_req = (
        '{"jsonrpc": "2.0", "method": "SportsAPING/v1.0/listMarketCatalogue", \
        "params": {"filter": {"venues": ["%s"], "marketTypeCodes": ["WIN", "PLACE"], "bspOnly": true}, \
        "maxResults": "1000", "sort":"FIRST_TO_START", \
        "marketProjection": ["RUNNER_DESCRIPTION", "MARKET_START_TIME"]}}'
        % (venue)
    )
    markets_response = call_api(markets_req, headers)
    try:
        market_type = markets_response["result"]
        for market in market_type:
            start_time = datetime.datetime.strptime(
                market["marketStartTime"], "%Y-%m-%dT%H:%M:%S.000Z"
            )
            if bool(time.localtime().tm_isdst):
                start_time += datetime.timedelta(0, 0, 0, 0, 0, 1)
            if race_time == start_time:
                markets.append(market)
        if len(markets) < 2:
            raise MatcherError("Not enough markets returned returned")
    except KeyError:
        try:
            print("Error in getting market: %s" % markets_response["error"])
        except KeyError:
            print("Unknown error getting market: %s" % markets_response)
        return None, None

    for market in markets:
        if market["marketName"] == "To Be Placed":
            markets_ids["Place"] = market["marketId"]
        else:
            markets_ids["Win"] = market["marketId"]
            horses = market
    return markets_ids, horses


def cancel_unmatched_bets(headers):
    cancel_req = '{"jsonrpc": "2.0", "method": "SportsAPING/v1.0/cancelOrders", "params": {}, "id": 7}'
    try:
        cancel_res = call_api(cancel_req, headers)
        if cancel_res["result"]["status"] == "SUCCESS":
            return True
    except (KeyError, MatcherError):
        print("ERROR: Could not cancel unmatched bets!")
        print(cancel_res)
    return False


def lay_bets(market_id, selection_id, price, stake, headers):
    matched = False
    bet_made = False
    stake_matched = 0
    matched_price = 0
    bet_req = (
        '{"jsonrpc": "2.0", "method": "SportsAPING/v1.0/placeOrders", \
        "params": {"marketId": "%s", "instructions": [{"selectionId": "%s", \
        "side": "LAY", "handicap": "0", "orderType": "LIMIT", "limitOrder": {"size": "%s", \
        "price": "%s", "persistenceType": "MARKET_ON_CLOSE"}}]}, "id": 1}'
        % (market_id, selection_id, round(stake, 2), price)
    )
    bet_res = call_api(bet_req, headers)
    try:
        if bet_res["result"]["status"] == "SUCCESS":
            bet_made = True
            stake_matched = bet_res["result"]["instructionReports"][0]["sizeMatched"]
            if stake_matched == stake:
                matched = True
            matched_price = round(
                float(
                    bet_res["result"]["instructionReports"][0]["averagePriceMatched"]
                ),
                2,
            )
            if price != matched_price:
                print("Odds have changed, original price: %s" % (price))

        elif bet_res["result"]["status"] == "FAILURE":
            print("Lay bet failed: %s" % bet_res["result"])

    except KeyError:
        try:
            print("Error in bet response: %s" % bet_res["error"])
        except KeyError:
            print("Unknown error making bet: %s" % bet_res)
            print()
            print(bet_req)
    return bet_made, matched_price, matched, stake_matched


def get_betfair_balance(headers):
    account_url = "https://api.betfair.com/exchange/account/json-rpc/v1"
    balance_req = '{"jsonrpc": "2.0", "method": "AccountAPING/v1.0/getAccountFunds"}'
    balance_res = call_api(balance_req, headers, url=account_url)
    balance = balance_res["result"]["availableToBetBalance"]
    return balance


def get_race(race_time, venue, horse):
    headers = login_betfair()
    race_time = datetime.datetime.strptime(race_time, "%d %b %H:%M %Y")
    markets_ids, horses = get_horses(venue, race_time, headers)
    selection_id, target_horse = get_horse_id(horses, horse)
    if selection_id is None:
        got_horse = False
    else:
        got_horse = True
    return markets_ids, selection_id, got_horse, target_horse


def lay_ew(markets_ids, selection_id, win_stake, win_odds, place_stake, place_odds):
    headers = login_betfair()
    lay_win, win_odds, win_matched, win_stake_matched = lay_bets(
        markets_ids["Win"], selection_id, round_stake(win_odds), win_stake, headers
    )
    lay_place, place_odds, place_matched, place_stake_matched = lay_bets(
        markets_ids["Place"],
        selection_id,
        round_stake(place_odds),
        place_stake,
        headers,
    )
    return (
        (lay_win, win_matched, win_stake, win_stake_matched, win_odds),
        (lay_place, place_matched, place_stake, place_stake_matched, place_odds),
    )
