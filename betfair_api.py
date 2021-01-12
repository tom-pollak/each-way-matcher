import datetime
import json
import os
from urllib import error, request

import requests
from dotenv import load_dotenv
from calculate_odds import round_stake

betting_url = "https://api.betfair.com/exchange/betting/json-rpc/v1"

load_dotenv(dotenv_path='.env')
APP_KEY = os.environ.get('APP_KEY')
USERNAME = os.environ.get('BETFAIR_USR')
PASSWORD = os.environ.get('BETFAIR_PASS')
if None in (USERNAME, PASSWORD, APP_KEY):
    raise Exception('betfair env vars not set')


def login_betfair():
    payload = f'username={USERNAME}&password={PASSWORD}'
    login_headers = {
        'X-Application': APP_KEY,
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    response = requests.post(
        'https://identitysso-cert.betfair.com/api/certlogin',
        data=payload,
        cert=('client-2048.crt', 'client-2048.key'),
        headers=login_headers)
    if response.status_code == 200:
        SESS_TOK = response.json()['sessionToken']
        return {
            'X-Application': APP_KEY,
            'X-Authentication': SESS_TOK,
            'content-type': 'application/json'
        }
    raise Exception("Can't login")


def output_lay_ew(race, betfair_balance, sporting_index_balance, profit,
                  win_bet_made, win_is_matched, win_stake, win_matched,
                  win_odds, place_bet_made, place_is_matched, place_stake,
                  place_matched, place_odds, win_profit, place_profit,
                  lose_profit):
    print(f"\nArb bet made: {race['horse_name']} - profit: £{profit}")
    print(f"\t{race['date_of_race']} - {race['race_venue']}")
    print(
        f"\tBack bookie: {race['horse_odds']} - {race['bookie_stake']} Lay win: {win_odds} - {win_stake} Lay place: {place_odds} - {place_stake}"
    )

    print(
        f"\tLay win: {win_bet_made} - is matched: {win_is_matched} Lay place: {place_bet_made} is matched: {place_is_matched}"
    )

    if not win_is_matched:
        print(f"\tLay win matched size: {win_matched} ", end='')
    if not place_is_matched:
        print(f"\tLay place matched size: {place_matched}")
    if not win_matched and place_matched:
        print()

    print(
        f"\tWin profit: {win_profit} Place profit: {place_profit} Lose profit: {lose_profit}"
    )
    print(
        f"Current balance: {sporting_index_balance}, betfair balance: {betfair_balance}\n"
    )


def call_api(jsonrpc_req, headers, url=betting_url):
    try:
        if url.lower().startswith('http'):
            req = request.Request(url, jsonrpc_req.encode('utf-8'), headers)
        else:
            raise ValueError('url does not start with http')
        with request.urlopen(req) as response:
            json_res = response.read()
            return json.loads(json_res.decode('utf-8'))
    except error.HTTPError:
        print('Not a valid operation' + str(url))
    except error.URLError as e:
        print(e.reason)
        print('No service available at ' + str(url))


def get_event(venue, race_time, headers):
    race_time_after = race_time + datetime.timedelta(0, 60)
    race_time = race_time.strftime('%Y-%m-%dT%H:%M:%SZ')
    race_time_after = race_time_after.strftime('%Y-%m-%dT%H:%M:%SZ')

    event_req = '{"jsonrpc": "2.0", "method": "SportsAPING/v1.0/listEvents", \
        "params": {"filter": {"eventTypeIds": ["7"], "marketTypeCodes": ["WIN"], \
        "marketStartTime": {"from": "%s", "to": "%s"}, "venues":["%s"]}, \
        "sort":"FIRST_TO_START","maxResults":"1"}}' % (race_time,
                                                       race_time_after, venue)
    event_response = call_api(event_req, headers)

    try:
        event_id = event_response['result'][0]['event']['id']
    except (KeyError, IndexError):
        try:
            print('Error in getting event: %s' % event_response['error'])
        except KeyError:
            print('Unknown error getting event: %s' % event_response)
        return False
    return event_id


def get_horse_id(horses, target_horse):
    for horse in horses['runners']:
        if horse['runnerName'].lower() == target_horse.lower():
            return horse['selectionId']

    # sometimes runnerName is 1. horse_name
    for horse in horses['runners']:
        if horse['runnerName'].lower() in target_horse.lower():
            return horse['selectionId']


def get_horses(target_horse, event_id, race_time, headers):
    markets_ids = {}
    race_time_after = race_time + datetime.timedelta(0, 60)
    race_time = race_time.strftime('%Y-%m-%dT%H:%M:%SZ')
    race_time_after = race_time_after.strftime('%Y-%m-%dT%H:%M:%SZ')

    markets_req = '{"jsonrpc": "2.0", "method": "SportsAPING/v1.0/listMarketCatalogue", \
        "params": {"filter":{"eventIds": ["%s"], "marketStartTime": {"from": "%s", "to": "%s"}}, \
        "maxResults": "10", "sort":"FIRST_TO_START", \
        "marketProjection": ["RUNNER_DESCRIPTION"]}}' % (event_id, race_time,
                                                         race_time_after)
    markets_response = call_api(markets_req, headers)

    try:
        market_type = markets_response['result']
    except IndexError:
        try:
            print('Error in getting market: %s' % markets_response['error'])
        except KeyError:
            print('Unknown error getting market: %s' % markets_response)
        return 0, 0, False

    total_matched = 0
    for i, market in enumerate(market_type):
        if market['marketName'] == 'Each Way':
            markets_ids['Each Way'] = market['marketId']
        elif market['marketName'] == 'To Be Placed':
            markets_ids['Place'] = market['marketId']
            market_type_index = i
        elif market['totalMatched'] > total_matched:
            markets_ids['Win'] = market['marketId']
            total_matched = market['totalMatched']

    selection_id = get_horse_id(market_type[market_type_index], target_horse)
    if selection_id is None:
        print("ERROR couldn't find horse selection_id")
        print(market_type[0]['runners'])
        return 0, 0, False
    return markets_ids, selection_id, True


def cancel_unmatched_bets(headers):
    cancel_req = '{"jsonrpc": "2.0", "method": "SportsAPING/v1.0/cancelOrders", "params": {}, "id": 7}'
    cancel_res = call_api(cancel_req, headers)
    try:
        if cancel_res['result']['status'] == 'SUCCESS':
            return True
        raise ValueError
    except (KeyError, ValueError):
        print('ERROR: could not cancel unmatched bets!')
        print(cancel_res)
        return False


def lay_bets(market_id, selection_id, price, stake, headers):
    matched = False
    bet_made = False
    stake_matched = 0
    bet_req = '{"jsonrpc": "2.0", "method": "SportsAPING/v1.0/placeOrders", \
        "params": {"marketId": "%s", "instructions": [{"selectionId": "%s", \
        "side": "LAY", "handicap": "0", "orderType": "LIMIT", "limitOrder": {"size": "%s", \
        "price": "%s", "persistenceType": "LAPSE"}}]}, "id": 1}' % (
        market_id, selection_id, round(stake, 2), price)
    bet_res = call_api(bet_req, headers)
    try:
        if bet_res['result']['status'] == 'SUCCESS':
            bet_made = True
            stake_matched = bet_res['result']['instructionReports'][0][
                'sizeMatched']
            if stake_matched == stake:
                matched = True
            matched_price = bet_res['result']['instructionReports'][0][
                'averagePriceMatched']
            if price - 1 != matched_price:
                print('Odds have changed, original price: %s' % price - 1)
        elif bet_res['result']['status'] == 'FAILURE':
            print(bet_req)
            print(bet_res)

    except KeyError:
        try:
            print('\tError in bet response: %s' % bet_res['error'])
        except KeyError:
            print('\tUnknown error making bet: %s' % bet_res)
    return bet_made, matched_price, matched, stake_matched


def get_betfair_balance(headers):
    account_url = 'https://api.betfair.com/exchange/account/json-rpc/v1'
    balance_req = '{"jsonrpc": "2.0", "method": "AccountAPING/v1.0/getAccountFunds"}'
    balance_res = call_api(balance_req, headers, url=account_url)
    balance = balance_res['result']['availableToBetBalance']
    return balance


def get_race(race_time, venue, horse):
    headers = login_betfair()
    race_time = datetime.datetime.strptime(race_time, '%d %b %H:%M %Y')
    event_id = get_event(venue, race_time, headers)
    if not event_id:
        return 0, 0, False

    markets_ids, selection_id, got_horse = get_horses(horse, event_id,
                                                      race_time, headers)
    return markets_ids, selection_id, got_horse


def lay_ew(markets_ids, selection_id, win_stake, win_odds, place_stake,
           place_odds):
    headers = login_betfair()
    lay_win, win_odds, win_matched, win_stake_matched = lay_bets(
        markets_ids['Win'], selection_id, round_stake(win_odds + 1), win_stake,
        headers)
    lay_place, place_odds, place_matched, place_stake_matched = lay_bets(
        markets_ids['Place'], selection_id, round_stake(place_stake + 1),
        place_stake, headers)
    return ((lay_win, win_matched, win_stake, win_stake_matched, win_odds),
            (lay_place, place_matched, place_stake, place_stake_matched,
             place_odds))


# markets_ids, selection_id, got_horse = get_race('12 Jan 12:30 2021',
#                                                 'Wetherby', 'Mont Segur')
# print(markets_ids, selection_id)
