import math
from datetime import datetime
from time import sleep, time, strptime
import pandas as pd

MIN_PERCENTAGE_BALANCE = 0
COMMISSION = 0.05

price_increments = {
    2: 0.01,
    3: 0.02,
    4: 0.05,
    6: 0.1,
    10: 0.2,
    20: 0.5,
    30: 1,
    50: 2,
    100: 5,
    1000: 10
}


def custom_date_parser(x):
    if '/' not in x:
        return datetime(*(strptime(x, '%d %b %H:%M %Y')[0:6]))
    return datetime(*(strptime(x, '%d/%m/%Y %H:%M:%S')[0:6]))


def check_repeat_bets(horse_name, date_of_race, race_venue):
    date_of_race = custom_date_parser(date_of_race)
    df = pd.read_csv(RETURNS_CSV,
                     header=0,
                     parse_dates=[7, 0],
                     index_col=7,
                     date_parser=custom_date_parser,
                     squeeze=True)
    mask = (df['horse_name']
            == horse_name) & (df['date_of_race'] == date_of_race) & (
                df['race_venue'] == race_venue) & (df['is_lay'] == False)
    if len(df.loc[mask]) == 0:
        return True
    if len(df.loc[mask]) > 1:
        print('ERROR more than one race matched')
        print(df.loc[mask])
    return False


def kelly_criterion(horse_odds, lay_odds, lay_odds_place, place_payout,
                    balance):
    n = 0.5 * (horse_odds - 1) / place_payout  # profit from place
    m = horse_odds * 0.5 - 0.5 + n  # profit from win
    n -= 0.5  # - the stake lost from losing win place

    p = 1 / lay_odds  # true odds of winning
    q = 1 / (lay_odds_place) - p  # true odds of placing

    A = m * n
    B = (p + q) * m * n + p * n + q * m - m - n
    C = p * m + q * n - (1 - p - q)  # Expected profit on 0.5 unit EW bet

    try:
        stake_proportion = (B + math.sqrt(B**2 + 4 * A * C)) / (4 * A)
    except ZeroDivisionError:  # if the profit from place is 0 then 0 division
        return 0, 0, '0%'
    ew_stake = stake_proportion * balance
    return round(ew_stake, 2), round(C * ew_stake * 2,
                                     2), str(round(C * 200, 2)) + '%'


def calculate_stakes(bookie_balance, betfair_balance, bookie_stake, win_stake,
                     win_odds, place_stake, place_odds):
    bookie_ratio = bookie_balance / bookie_stake
    liabiltity_ratio = 1

    max_win_liability = (win_odds - 1) * win_stake
    max_place_liability = (place_odds - 1) * place_stake
    total_liability = max_win_liability + max_place_liability

    if total_liability > betfair_balance:
        liabiltity_ratio = betfair_balance / total_liability
    if bookie_ratio < liabiltity_ratio:
        liabiltity_ratio = bookie_ratio

    # maximum possible stakes
    bookie_stake *= liabiltity_ratio
    win_stake *= liabiltity_ratio
    place_stake *= liabiltity_ratio
    max_stake = bookie_stake * 2 + win_stake + place_stake

    lay_min_stake_proportion = 0
    bookie_min_stake_proportion = 0.1 / bookie_stake

    if max_win_liability >= 10 and max_place_liability >= 10:
        lay_min_stake_proportion = 10 / min(max_win_liability,
                                            max_place_liability)
    if win_stake >= 2 and place_stake >= 2:
        stake_min_stake_proportion = 2 / min(win_stake, place_stake)
        if lay_min_stake_proportion != 0:  # Eligible for > 10 liability
            lay_min_stake_proportion = min(lay_min_stake_proportion,
                                           stake_min_stake_proportion)
        else:
            lay_min_stake_proportion = stake_min_stake_proportion

    if lay_min_stake_proportion == 0:  # Stake not above 2 or liability above 10
        print(
            f'\tStakes too small: win stake - £{win_stake} place_stake - £{place_stake}'
        )
        return False, 0, 0, 0

    min_stake_proportion = max(bookie_min_stake_proportion,
                               lay_min_stake_proportion)
    min_stake = min_stake_proportion * max_stake
    min_balance_staked = MIN_PERCENTAGE_BALANCE * (betfair_balance +
                                                   bookie_balance)
    if min_balance_staked > min_stake:
        if min_balance_staked >= max_stake:
            min_stake_proportion = 1
        else:
            min_stake_proportion = max_stake / min_balance_staked

    bookie_stake *= min_stake_proportion
    win_stake *= min_stake_proportion
    place_stake *= min_stake_proportion
    return True, round(bookie_stake, 2), round(win_stake,
                                               2), round(place_stake, 2)


def round_stake(odd):
    for price in price_increments:
        if odd < price:
            return round(
                round(odd / price_increments[price]) * price_increments[price],
                2)


def get_next_odd_increment(odd):
    for price in price_increments:
        if odd < price:
            return round(odd + price_increments[price], 2)


# N.B bookie_stake is half actual stake
def calculate_profit(bookie_odds, bookie_stake, win_odds, win_stake,
                     place_odds, place_stake, place_payout):
    commision = (win_stake + place_stake) * COMMISSION
    place_profit = bookie_stake * (bookie_odds - 1) / place_payout
    win_profit = bookie_odds * bookie_stake - bookie_stake + place_profit
    place_profit -= bookie_stake

    win_profit -= win_stake * (win_odds - 1) + place_stake * (place_odds -
                                                              1) + commision
    place_profit += win_stake - place_stake * (place_odds - 1) - commision

    lose_profit = win_stake + place_stake - bookie_stake * 2 - commision
    return round(win_profit, 2), round(place_profit, 2), round(lose_profit, 2)


# print(kelly_criterion(21, 21, 4, 4, 43))
# profits = calculate_profit(5.5, 2.05, 5.38, 2, 1.77, 2.11, 4)
