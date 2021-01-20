from betfair_api import get_betfair_balance, login_betfair
from sporting_index import get_balance_sporting_index
from csv import DictWriter

RETURNS_CSV = 'returns/returns.csv'


def update_csv_sporting_index(driver, race):
    headers = login_betfair()
    race['is_lay'] = False
    race['win_matched'] = 0
    race['lay_matched'] = 0
    race['arbritrage_profit'] = 0
    race['balance'] = get_balance_sporting_index(driver)
    race['betfair_balance'] = get_betfair_balance(headers)
    csv_columns = [
        'date_of_race', 'horse_name', 'horse_odds', 'race_venue', 'ew_stake',
        'balance', 'rating', 'current_time', 'expected_value',
        'expected_return', 'win_stake', 'place_stake', 'lay_odds',
        'lay_odds_place', 'betfair_balance', 'max_profit', 'is_lay',
        'win_matched', 'lay_matched', 'arbritrage_profit', 'place_paid'
    ]
    with open(RETURNS_CSV, 'a+', newline='') as returns_csv:
        csv_writer = DictWriter(returns_csv,
                                fieldnames=csv_columns,
                                extrasaction='ignore')
        csv_writer.writerow(race)


def update_csv_betfair(race, sporting_index_balance, bookie_stake, win_stake,
                       place_stake, betfair_balance, win_matched, lay_matched,
                       arbritrage_profit, win_odds, place_odds):
    race['is_lay'] = True
    race['ew_stake'] = bookie_stake
    race['win_stake'] = win_stake
    race['place_stake'] = place_stake
    race['betfair_balance'] = betfair_balance
    race['balance'] = sporting_index_balance
    race['win_matched'] = win_matched
    race['lay_matched'] = lay_matched
    race['arbritrage_profit'] = arbritrage_profit
    race['expected_value'] = race['expected_return'] = 0
    race['lay_odds'] = win_odds
    race['lay_odds_place'] = place_odds
    csv_columns = [
        'date_of_race', 'horse_name', 'horse_odds', 'race_venue', 'ew_stake',
        'balance', 'rating', 'current_time', 'expected_value',
        'expected_return', 'win_stake', 'place_stake', 'lay_odds',
        'lay_odds_place', 'betfair_balance', 'max_profit', 'is_lay',
        'win_matched', 'lay_matched', 'arbritrage_profit', 'place_paid'
    ]
    with open(RETURNS_CSV, 'a+', newline='') as returns_csv:
        csv_writer = DictWriter(returns_csv,
                                fieldnames=csv_columns,
                                extrasaction='ignore')
        csv_writer.writerow(race)
