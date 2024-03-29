from datetime import datetime, timedelta
import json
import os
import requests
import time
import ast

from http.client import RemoteDisconnected
from urllib import error, request
from dotenv import load_dotenv

from matcher.exceptions import MatcherError
from matcher.calculate import round_odd, write_new_headers

betting_url = "https://api.betfair.com/exchange/betting/json-rpc/v1"

venue_names = {
    "Cagnes-Sur-Mer": "Cagnes Sur Mer",
    "Bangor-On-Dee": "Bangor-on-Dee",
    "Bangor": "Bangor-on-Dee",
    "Chelmsford": "Chelmsford City",
}

BASEDIR = os.path.abspath(os.path.dirname(__file__) + "/../../")
load_dotenv(os.path.join(BASEDIR, ".env"))

APP_KEY = os.environ.get("APP_KEY")
USERNAME = os.environ.get("BETFAIR_USR")
PASSWORD = os.environ.get("BETFAIR_PASS")
try:
    HEADERS = ast.literal_eval(os.environ.get("HEADERS"))
except (ValueError, SyntaxError):
    HEADERS = {}
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
    raise MatcherError("Can't login: %s" % response.status_code)


def call_api(jsonrpc_req, url=betting_url):
    global HEADERS
    # HEADERS = login()  # delete line
    log = ""
    for _ in range(5):
        try:
            if url.lower().startswith("http"):
                req = request.Request(url, jsonrpc_req.encode("utf-8"), HEADERS)
            else:
                raise MatcherError("url does not start with http")
            try:
                with request.urlopen(req) as response:
                    json_res = response.read()
                    res = json.loads(json_res.decode("utf-8"))
                    if res.get("error"):
                        exception_name = res["error"]["data"]["exceptionname"]
                        if res["error"]["data"][exception_name]["errorCode"] in [
                            "INVALID_SESSION_INFORMATION",
                            "NO_SESSION",
                            "NO_APP_KEY",
                        ]:
                            HEADERS = login()
                            write_new_headers(HEADERS)
                            return call_api(jsonrpc_req, url=url)
                    return res
            except RemoteDisconnected as e:
                raise MatcherError("API request failed: %s" % e)

        except error.HTTPError as e:
            err = f"\nRequest failed with response: {e.response.status_code}\n{url}"
            if err not in log:
                log += err
            continue
        except error.URLError:
            err = f"\nNo service available at {url}"
            if err not in log:
                log += err
            continue
    print(log)
    raise MatcherError("API request failed: %s\n" % jsonrpc_req)


def get_balance():
    account_url = "https://api.betfair.com/exchange/account/json-rpc/v1"
    balance_req = '{"jsonrpc": "2.0", "method": "AccountAPING/v1.0/getAccountFunds"}'
    balance_res = call_api(balance_req, url=account_url)
    try:
        balance = balance_res["result"]["availableToBetBalance"]
        return balance
    except KeyError:
        raise MatcherError("Couldn't get Betfair balance: %s" % balance_res)


def get_exposure():
    account_url = "https://api.betfair.com/exchange/account/json-rpc/v1"
    exposure_req = '{"jsonrpc": "2.0", "method": "AccountAPING/v1.0/getAccountFunds"}'
    exposure_res = call_api(exposure_req, url=account_url)
    exposure = abs(exposure_res["result"]["exposure"])
    return exposure


def cancel_unmatched_bets():
    cancel_req = '{"jsonrpc": "2.0", "method": "SportsAPING/v1.0/cancelOrders", "params": {}, "id": 7}'
    try:
        cancel_res = call_api(cancel_req)
        if cancel_res["result"]["status"] == "SUCCESS":
            return True
    except (KeyError, MatcherError):
        print("ERROR: Could not cancel unmatched bets!\n %s" % cancel_res)
    return False


def get_odds(market_id, selection_id):
    price_req = (
        '{"jsonrpc": "2.0", "method": "SportsAPING/v1.0/listRunnerBook", "params": {"locale":"en", "marketId": "%s", "selectionId": "%s", "priceProjection": {"priceData":["EX_BEST_OFFERS"], "virtualise":"true"}, "orderProjection":"ALL"},"id":1}'
        % (market_id, int(selection_id))
    )
    res = call_api(price_req)
    try:
        odds = res["result"][0]["runners"][0]["ex"]["availableToLay"][0]
    except IndexError:
        return 9999, 0
    except KeyError:
        raise MatcherError("Couldn't get odds from betfair:\n%s" % res)
    return odds["price"], odds["size"]


def get_race(venue, race_time):
    markets_ids = get_market_id(venue, race_time)
    horses = get_horses(venue, race_time)
    horses = {i: k for k, i in horses.items()}

    runners = {}
    price_req = (
        '{"jsonrpc": "2.0", "method": "SportsAPING/v1.0/listMarketBook", "params": {"locale":"en", "marketIds": ["%s", "%s"], "priceProjection": {"priceData":["EX_BEST_OFFERS"], "virtualise":"true"}},"id":1}'
        % (markets_ids["win"], markets_ids["place"])
    )
    res = call_api(price_req)
    # for r in res["result"]:
    for i, r in enumerate(res["result"]):
        if i == 0:
            m_type = "win"
        else:
            m_type = "place"
        for runner in r["runners"]:
            try:
                sel_id, price = (
                    runner["selectionId"],
                    runner["ex"]["availableToLay"][0]["price"],
                )
                # name =
                try:
                    if i == 0:
                        runners[horses[sel_id]] = {m_type: price}
                    else:
                        runners[horses[sel_id]][m_type] = price
                except KeyError:
                    print("No odds for ", horses[sel_id])

            except IndexError:
                continue
    return runners
    # try:
    #     odds = res["result"][0]["runners"][0]["ex"]["availableToLay"][0]
    # except IndexError:
    #     return 9999, 0
    # except KeyError:
    #     raise MatcherError("Couldn't get odds from betfair:\n%s" % res)
    # return odds["price"], odds["size"]


def check_odds(race, market_ids, selection_id):
    win_odds, win_available = get_odds(market_ids["win"], selection_id)
    place_odds, place_available = get_odds(market_ids["place"], selection_id)
    try:
        if (
            win_odds <= race["win_odds"]
            and place_odds <= race["place_odds"]
            and win_available >= race["win_stake"]
            and place_available >= race["place_stake"]
        ):
            return True
    except KeyError as e:
        print("ERROR scraping betfair %s" % e)
    return False


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
    return win_stake, round(win_odds, 2), place_stake, round(place_odds, 2)


def get_bets_by_bet_id(win_market_id, place_market_id, *bet_ids):
    bet_ids = [int(x) for x in bet_ids if x is not None]
    bet_info = {}
    order_req = (
        '{"jsonrpc": "2.0", "method": "SportsAPING/v1.0/listCurrentOrders", "params": {"betIds": %s}, "id": 1}'
        % bet_ids
    )
    bets = call_api(order_req)["result"]["currentOrders"]
    for bet in bets:
        odds = bet["averagePriceMatched"]
        stake = bet["sizeMatched"]
        temp = {"odds": odds, "stake": stake}
        if bet["marketId"] == win_market_id:
            bet_info["win"] = temp
        elif bet["marketId"] == place_market_id:
            bet_info["place"] = temp
    return bet_info


def get_daily_races():
    req = '{"jsonrpc": "2.0", "method": "SportsAPING/v1.0/listMarketCatalogue", \
        "params": {"filter": {"eventTypeIds": ["7"], "marketTypeCodes": ["WIN", "PLACE"], "bspOnly": true}, \
        "maxResults": "10000", "sort":"FIRST_TO_START", \
        "marketProjection": ["RUNNER_DESCRIPTION", "MARKET_START_TIME"]}}'
    res = call_api(req)
    print(res)


def get_market_id(venue, race_time):
    markets = []
    markets_ids = {}
    if venue_names.get(venue) is not None:
        venue = venue_names.get(venue)
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
            start_time = datetime.strptime(
                market["marketStartTime"], "%Y-%m-%dT%H:%M:%S.000Z"
            )
            if bool(time.localtime().tm_isdst):
                start_time += timedelta(0, 0, 0, 0, 0, 1)
            if race_time == start_time:
                markets.append(market)
        if len(markets) < 2:
            raise MatcherError("Not enough markets returned")
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
    return markets_ids


def lay_bets(market_id, selection_id, price, stake):
    matched = False
    bet_made = False
    stake_matched = 0
    matched_price = 0
    bet_id = None
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
        elif bet_res["result"]["status"] == "FAILURE":
            print("Lay bet failed: %s" % bet_res["result"])

    except KeyError:
        try:
            print("Error in bet response: %s\n" % bet_res["error"])
        except KeyError:
            print("Unknown error making bet: %s\n" % bet_res)
            print(bet_req)
    return bet_made, matched_price, matched, stake_matched, bet_id


def get_horses(venue, race_time):
    market_ids = get_market_id(venue, race_time)
    horses_req = (
        '{"jsonrpc": "2.0", "method": "SportsAPING/v1.0/listMarketCatalogue", \
        "params": {"filter": {"marketIds": ["%s"]}, \
        "maxResults": "1", "sort":"FIRST_TO_START", \
        "marketProjection": ["RUNNER_DESCRIPTION", "RUNNER_METADATA"]}}'
        % (market_ids["win"])
    )
    horses_res = call_api(horses_req)["result"][0]["runners"]
    horses = {horse["runnerName"]: horse["selectionId"] for horse in horses_res}
    return horses


def get_race_ids(race_time, venue, horse):
    markets_ids = get_market_id(venue, race_time)
    horses = get_horses(venue, race_time)
    try:
        selection_id = horses[horse]
    except KeyError:
        print(f"Can't get horse selection id: {horse}\n{horses}")
        raise MatcherError("Can't get selection id")
    return markets_ids, selection_id


def make_bet(markets_ids, selection_id, win_stake, win_odds, place_stake, place_odds):
    win_dict = place_dict = {"matched": True, "bet_id": None}
    if win_stake:
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

    if place_stake:
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
