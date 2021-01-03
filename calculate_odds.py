import datetime
import time
import math
import pandas as pd

MIN_PERCENTAGE_BALANCE = 0
RETURNS_CSV = 'returns/returns.csv'


def custom_date_parser(x):
    return datetime.datetime(*(time.strptime(x, '%d/%m/%Y %H:%M:%S')[0:6]))


def kelly_criterion(horse_odds, lay_odds, lay_odds_place, place, balance):
    n = 0.5 * (horse_odds - 1) / place  # profit from place
    m = horse_odds * 0.5 - 0.5 + n  # profit from win
    n -= 0.5  # - the stake lost from losing win place
    # print(m, n)

    p = 1 / lay_odds  # true odds of winning
    q = 1 / (lay_odds_place) - p  # true odds of placeing
    # print(p, q)

    A = m * n
    B = (p + q) * m * n + p * n + q * m - m - n
    C = p * m + q * n - (1 - p - q)  # Expected profit on 0.5 unit EW bet
    # print(A, B, C)

    try:
        stake_proportion = (B + math.sqrt(B**2 + 4 * A * C)) / (4 * A)
    except ZeroDivisionError:  # if the profit from place is 0 then 0 division
        print('ERROR Divided by 0')
        return 0, 0, '0%'
    # print(stake_proportion)
    ew_stake = stake_proportion * balance
    # print(ew_stake)
    return round(ew_stake, 2), round(C * ew_stake * 2,
                                     2), str(round(C * 200, 2)) + '%'


def calculate_stakes(bookie_balance, betfair_balance, bookie_stake, win_stake,
                     win_odds, place_stake, place_odds, avaliable_profit):
    max_profit_ratio = avaliable_profit / win_stake
    max_win_liability = (win_odds - 1) * win_stake
    max_place_liability = (place_odds - 1) * place_stake
    total_liability = max_win_liability + max_place_liability

    # bookie_ratio = 1
    # win_ratio = win_stake / bookie_stake
    # place_ratio = place_stake / bookie_stake

    if total_liability > betfair_balance or bookie_stake > bookie_balance:
        liabiltity_ratio = betfair_balance / total_liability
        balance_ratio = bookie_stake / bookie_balance
        if balance_ratio < liabiltity_ratio:
            liabiltity_ratio = balance_ratio
    else:
        liabiltity_ratio = 1

    # maximum possible stakes
    bookie_stake *= liabiltity_ratio
    win_stake *= liabiltity_ratio
    place_stake *= liabiltity_ratio

    if win_stake >= 2 and place_stake >= 2 and bookie_stake >= 0.1:
        min_stake_proportion = max(2 / min(win_stake, place_stake),
                                   0.1 / bookie_stake)
        min_stake = min_stake_proportion * (bookie_stake + win_stake +
                                            place_stake)
        min_balance_staked = MIN_PERCENTAGE_BALANCE * (betfair_balance +
                                                       bookie_balance)
        if min_stake < min_balance_staked:
            min_stake_proportion = MIN_PERCENTAGE_BALANCE

        bookie_stake *= min_stake_proportion
        win_stake *= min_stake_proportion
        place_stake *= min_stake_proportion
        profit = max_profit_ratio * win_stake
        if profit <= 0:
            return False, 0, 0, 0, 0
        return True, round(bookie_stake,
                           2), round(win_stake, 2), round(place_stake,
                                                          2), round(profit, 2)
    print('Stakes are too small to bet')
    print(
        f'Bookie stake: {round(bookie_stake, 2)} Win stake: {round(win_stake, 2)} Place stake: {round(place_stake, 2)}\n'
    )
    return False, 0, 0, 0, 0


def output_profit():
    df = pd.read_csv(RETURNS_CSV,
                     header=0,
                     parse_dates=[7],
                     index_col=7,
                     date_parser=custom_date_parser,
                     squeeze=True)
    today = pd.date_range(datetime.datetime.now().strftime('%Y-%m-%d'),
                          periods=1)

    # print([df['balance'].isin(today).values[0]])
    starting_balance = df['balance'].values[0] + df['betfair_balance'].values[0]
    today_starting_balance = df.loc[datetime.datetime.now().strftime(
        '%Y-%m-%d')]['balance'].values[0] + df.loc[datetime.datetime.now(
        ).strftime('%Y-%m-%d')]['betfair_balance'].values[0]

    current_balance = df['balance'].values[-1] + df['betfair_balance'].values[
        -1]
    total_profit = current_balance - starting_balance
    profit_today = current_balance - today_starting_balance
    print(f'Total profit: {total_profit}')
    print(f'Profit today: {profit_today}')


# kelly_criterion(12, 12, 3.2, 5, 10000)
