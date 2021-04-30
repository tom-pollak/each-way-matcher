import datetime
import json
import os
import difflib
import requests
import time

from urllib import error, request
from dotenv import load_dotenv
from json.decoder import JSONDecodeError

from matcher.exceptions import MatcherError
from matcher.calculate import round_odd

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


def login():
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


def get_odds(market_id):
    horses = {}
    resp = requests.get(
        f"https://www.betfair.com/www/sports/exchange/readonly/v1/bymarket?_ak=nzIFcwyWhrlwYMrh&alt=json&currencyCode=GBP&locale=en_GB&marketIds={market_id}&rollupLimit=10&rollupModel=STAKE&types=EVENT,RUNNER_DESCRIPTION,%20RUNNER_EXCHANGE_PRICES_BEST"
    )
    try:
        horses_resp = resp.json()["eventTypes"][0]["eventNodes"][0]["marketNodes"][0][
            "runners"
        ]
    except JSONDecodeError:
        print(json)
        raise MatcherError("Couldn't decode JSON")

    for horse in horses_resp:
        horse_name = horse["description"]["runnerName"]
        horses[horse_name] = {
            "back_odds_1": 0,
            "back_odds_2": 0,
            "back_odds_3": 0,
            "lay_odds_1": 99999,
            "lay_odds_2": 99999,
            "lay_odds_3": 99999,
            "back_avaliable_1": 0,
            "back_avaliable_2": 0,
            "back_avaliable_3": 0,
            "lay_avaliable_1": 0,
            "lay_avaliable_2": 0,
            "lay_avaliable_3": 0,
        }
        back = horse["exchange"].get("availableToBack")
        lay = horse["exchange"].get("availableToLay")
        if back is not None:
            for i, odds in enumerate(back):
                horses[horse_name][f"back_odds_{i+1}"] = odds["price"]
                horses[horse_name][f"back_avaliable_{i+1}"] = odds["size"]
        if lay is not None:
            for i, odds in enumerate(lay):
                horses[horse_name][f"lay_odds_{i+1}"] = odds["price"]
                horses[horse_name][f"lay_avaliable_{i+1}"] = odds["size"]
    return horses


def call_api(jsonrpc_req, url=betting_url):
    headers = login()
    try:
        if url.lower().startswith("http"):
            req = request.Request(url, jsonrpc_req.encode("utf-8"), headers)
        else:
            raise MatcherError("url does not start with http")
        with request.urlopen(req) as response:
            json_res = response.read()
            return json.loads(json_res.decode("utf-8"))
    except error.HTTPError:
        print("Not a valid operation " + str(url))
    except error.URLError:
        print("No service available at " + str(url))
    print(jsonrpc_req)
    raise MatcherError("API request failed")


def get_balance_in_bets():
    balance_in_bets = 0
    order_req = '{"jsonrpc": "2.0", "method": "SportsAPING/v1.0/listCurrentOrders"}'
    res = call_api(order_req)
    for race in res["result"]["currentOrders"]:
        odds = race["averagePriceMatched"]
        stake = race["sizeMatched"]
        stake_remaining = race["sizeRemaining"]
        original_odds = race["priceSize"]["price"]

        balance_in_bets += stake * (odds - 1) + stake_remaining * (original_odds - 1)
    return balance_in_bets


def get_bets_by_race(win_market_id, place_market_id):
    bet_info = {"win": [], "place": []}
    order_req = (
        '{"jsonrpc": "2.0", "method": "SportsAPING/v1.0/listCurrentOrders", "params": {"marketIds": ["%s", "%s"]}, "id": 1}'
        % (win_market_id, place_market_id)
    )
    bets = call_api(order_req)["result"]["currentOrders"]
    print(bets)
    for bet in bets:
        odds = bet["averagePriceMatched"]
        stake = bet["sizeMatched"]
        temp = {"odds": odds, "stake": stake}
        if bet["marketId"] == win_market_id:
            bet_info["win"].append(temp)
        else:
            bet_info["place"].append(temp)
    win_stake = place_stake = win_odds = place_odds = 0
    for win_bet, place_bet in zip(bet_info["win"], bet_info["place"]):
        win_stake += win_bet["stake"]
        place_stake += place_bet["stake"]
        win_odds += win_bet["stake"] * win_bet["odds"]
        place_odds += place_bet["stake"] * place_bet["odds"]
    win_odds /= win_stake
    place_odds /= place_stake
    return win_stake, win_odds, place_stake, place_odds


def get_bets_by_bet_id(win_bet_id, place_bet_id):
    bet_info = {}
    order_req = (
        '{"jsonrpc": "2.0", "method": "SportsAPING/v1.0/listCurrentOrders", "params": {"betIds": ["%s", "%s"]}, "id": 1}'
        % (win_bet_id, place_bet_id)
    )
    bets = call_api(order_req)["result"]["currentOrders"]
    for bet in bets:
        odds = bet["averagePriceMatched"]
        stake = bet["sizeMatched"]
        temp = {"odds": odds, "stake": stake}
        if bet["betId"] == win_bet_id:
            bet_info["win"] = temp
        elif bet["bet_id"] == place_bet_id:
            bet_info["place"] = temp
    return bet_info


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


def get_horses(venue, race_time):
    markets = []
    markets_ids = {}
    markets_req = (
        '{"jsonrpc": "2.0", "method": "SportsAPING/v1.0/listMarketCatalogue", \
        "params": {"filter": {"venues": ["%s"], "marketTypeCodes": ["WIN", "PLACE"], "bspOnly": true}, \
        "maxResults": "1000", "sort":"FIRST_TO_START", \
        "marketProjection": ["RUNNER_DESCRIPTION", "MARKET_START_TIME"]}}'
        % (venue)
    )
    markets_response = call_api(markets_req)
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
            markets_ids["place"] = market["marketId"]
        else:
            markets_ids["win"] = market["marketId"]
            horses = market
    return markets_ids, horses


def cancel_unmatched_bets():
    cancel_req = '{"jsonrpc": "2.0", "method": "SportsAPING/v1.0/cancelOrders", "params": {}, "id": 7}'
    try:
        cancel_res = call_api(cancel_req)
        print(cancel_res)
        if cancel_res["result"]["status"] == "SUCCESS":
            return True
    except (KeyError, MatcherError):
        print("ERROR: Could not cancel unmatched bets!")
        print(cancel_res)
    return False


def lay_bets(market_id, selection_id, price, stake):
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
    bet_res = call_api(bet_req)
    try:
        if bet_res["result"]["status"] == "SUCCESS":
            bet_made = True
            bet_id = bet_res["result"]["instructionReports"][0]["betId"]
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
    return bet_made, matched_price, matched, stake_matched, bet_id


def get_balance():
    account_url = "https://api.betfair.com/exchange/account/json-rpc/v1"
    balance_req = '{"jsonrpc": "2.0", "method": "AccountAPING/v1.0/getAccountFunds"}'
    balance_res = call_api(balance_req, url=account_url)
    balance = balance_res["result"]["availableToBetBalance"]
    return balance


def get_race_ids(race_time, venue, horse):
    race_time = datetime.datetime.strptime(race_time, "%d %b %H:%M %Y")
    markets_ids, horses = get_horses(venue, race_time)
    selection_id, target_horse = get_horse_id(horses, horse)
    if selection_id is None:
        got_horse = False
    else:
        got_horse = True
    return markets_ids, selection_id, got_horse, target_horse


def make_bets(markets_ids, selection_id, win_stake, win_odds, place_stake, place_odds):
    win_dict = place_dict = {"matched": True, "bet_id": None}
    if win_stake is not None:
        lay_win, win_odds, win_matched, win_stake_matched, win_bet_id = lay_bets(
            markets_ids["win"], selection_id, round_odd(win_odds), win_stake
        )
        win_dict = {
            "success": lay_win,
            "matched": win_matched,
            "total_stake": win_stake,
            "matched_stake": win_stake_matched,
            "odds": win_odds,
            "bet_id": win_bet_id,
        }

    if place_stake is not None:
        (
            lay_place,
            place_odds,
            place_matched,
            place_stake_matched,
            place_bet_id,
        ) = lay_bets(
            markets_ids["place"],
            selection_id,
            round_odd(place_odds),
            place_stake,
        )
        place_dict = {
            "success": lay_place,
            "matched": place_matched,
            "total_stake": place_stake,
            "matched_stake": place_stake_matched,
            "odds": place_odds,
            "bet_id": place_bet_id,
        }
    return win_dict, place_dict