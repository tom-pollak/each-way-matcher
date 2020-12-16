from urllib import request, error
import json
import datetime
import sys
import os
from dotenv import load_dotenv

url = "https://api.betfair.com/exchange/betting/json-rpc/v1"

load_dotenv(dotenv_path='.env')
APP_KEY = os.environ.get('APP_KEY')
SESS_TOK = os.environ.get('SESS_TOK')
headers = {
    'X-Application': APP_KEY,
    'X-Authentication': SESS_TOK,
    'content-type': 'application/json'
}


def call_api(jsonrpc_req):
    try:
        req = request.Request(url, jsonrpc_req.encode('utf-8'), headers)
        response = request.urlopen(req)
        json_res = response.read()
        return json_res.decode('utf-8')
    except error.URLError as e:
        print(e.reason)
        print('No service available at ' + str(url))
        exit()
    except error.HTTPError:
        print('Not a valid operation' + str(url))
        exit()


def get_event(venue, race_time):
    race_time_after = race_time + datetime.timedelta(0, 60)
    race_time = race_time.strftime('%Y-%m-%dT%H:%M:%SZ')
    race_time_after = race_time_after.strftime('%Y-%m-%dT%H:%M:%SZ')

    event_req = '{"jsonrpc": "2.0", "method": "SportsAPING/v1.0/listEvents", \
        "params": {"filter": {"eventTypeIds": ["7"], "marketTypeCodes": ["EACH_WAY"], \
        "marketStartTime": {"from": "%s", "to": "%s"}, "venues":["%s"]}, \
        "sort":"FIRST_TO_START","maxResults":"1"}}' % (
        race_time, race_time_after, venue)
    event_response = json.loads(call_api(event_req))

    try:
        event_id = event_response['result'][0]['event']['id']
    except:
        print('Exception from API-NG' + str(event_response['result']['error']))
    return event_id


def get_horse_id(horses, target_horse):
    for horse in horses['runners']:
        if horse['runnerName'] == target_horse:
            return horse['selectionId']


def get_horses(target_horse, event_id, race_time):
    markets_ids = {}
    race_time_after = race_time + datetime.timedelta(0, 60)
    race_time = race_time.strftime('%Y-%m-%dT%H:%M:%SZ')
    race_time_after = race_time_after.strftime('%Y-%m-%dT%H:%M:%SZ')

    markets_req = '{"jsonrpc": "2.0", "method": "SportsAPING/v1.0/listMarketCatalogue", \
        "params": {"filter":{"eventIds": ["%s"], "marketStartTime": {"from": "%s", "to": "%s"}}, \
        "maxResults": "10", "sort":"FIRST_TO_START", \
        "marketProjection": ["RUNNER_DESCRIPTION"]}}' % (
        event_id, race_time, race_time_after)
    markets_response = json.loads(call_api(markets_req))

    try:
        market_type = markets_response['result']
        if len(market_type) != 3:
            print(market_type)
            raise Exception('Only %s market types returned' % len(market_type))
    except IndexError:
        print('Exception from API-NG' +
              str(markets_response['result']['error']))

    for market in market_type:
        if market['marketName'] == 'Each Way':
            markets_ids['Each Way'] = market['marketId']
        elif market['marketName'] == 'To Be Placed':
            markets_ids['Place'] = market['marketId']
        else:
            markets_ids['Win'] = market['marketId']

    selection_id = get_horse_id(market_type[0], target_horse)
    return markets_ids, selection_id


def lay_bets(market_id, selection_id, price, stake):
    bet_req = '{"jsonrpc": "2.0", "method": "SportsAPING/v1.0/placeOrders", \
        "params": {"marketId": "%s", "instructions": [{"selectionId": "%s", \
        "side": "LAY", "orderType": "LIMIT", "limitOrder": {"size": "%s", \
        "price": "%s", "persistenceType": "LAPSE"}}]}}' % (
        market_id, selection_id, stake, price)
    bet_res = json.loads(call_api(bet_req))
    print(bet_res)
    try:
        if bet_res['result']['status'] == 'SUCCESS':
            print('Bet made')
            return True
        else:
            return False
    except KeyError:
        print('Error:' + bet_res['error'])
        return False


def get_betfair_balance():
    pass


def calculate_proportinate_stake(bookie_balance,
                                 betfair_balance,
                                 bookie_stake,
                                 win_stake,
                                 place_stake):
    return bookie_stake, win_stake, place_stake


def lay_each_way(bookie_balance,
                 race_time,
                 venue,
                 horse,
                 win_stake,
                 win_odds,
                 bookie_stake,
                 bookie_odds,
                 place_stake,
                 place_odds):
    if not isinstance(datetime.datetime.now(), race_time):
        raise Exception('race_time is not a datetime instance')
    betfair_balance = get_betfair_balance()
    bookie_stake, win_stake, place_stake= calculate_proportinate_stake(bookie_balance,
                                 betfair_balance,
                                 bookie_stake,
                                 win_stake,
                                 place_stake)
    if float(win_stake) < 2 or float(place_stake) < 2:
        print('Stakes are to small to bet')
        return False

    event_id = get_event(venue, race_time)
    markets_ids, selection_id = get_horses(horse, event_id, race_time)
    lay_win = lay_bets(markets_ids['Win'], selection_id, win_odds, win_stake)
    lay_place = lay_bets(markets_ids['Place'],
                         selection_id,
                         place_odds,
                         place_stake)
    print('Lay win: %s\tLay place: %s' % (lay_win, lay_place))
    return lay_win and lay_place


# Testing variables
# race_time = datetime.datetime(2020, 12, 16, 16)
# venue = 'Kempton'
# horse = 'Touchwood'
#
# event_id = get_event(venue, race_time)
# markets_ids, selection_id = get_horses(horse, event_id, race_time)
# print(markets_ids, selection_id)
