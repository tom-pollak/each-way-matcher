import os
import sys
from datetime import datetime

import pandas as pd

from .calculate import custom_date_parser


def calc_unfinished_races(index=-1):
    races_liability = {}
    in_bet_balance = 0
    mask = (df['date_of_race'] >
            df.index.values[index]) & (df.index <= df.index.values[index])
    races = df.loc[mask]
    for _, row in races.iterrows():
        stake = row['ew_stake'] * 2
        if row['is_lay']:
            liability = row['win_stake'] * (row['win_odds'] - 1)
            lia_key = '%s %s' % (row['venue'], row['date_of_race'])
            if lia_key in races_liability:
                if liability > races_liability[lia_key]:
                    liability -= races_liability[lia_key]
                else:
                    liability = 0
                races_liability[lia_key] += liability
            else:
                races_liability[lia_key] = liability

            liability += row['place_stake'] * (row['place_odds'] - 1)
        else:
            liability = 0
        in_bet_balance += (stake + liability)
    return round(in_bet_balance, 2)


def output_profit(current_sporting_index_balance=False):
    def get_today_starting_balance():
        try:
            today_first_bet = df.loc[datetime.now().strftime(
                '%Y-%m-%d')].index.values[0]
        except KeyError:
            return None
        count = 0
        for index, _ in df.iterrows():
            if today_first_bet == index:
                break
            count += 1

        return df.loc[datetime.now().strftime(
            '%Y-%m-%d')]['balance'].values[0] + df.loc[datetime.now().strftime(
                '%Y-%m-%d'
            )]['betfair_balance'].values[0] + calc_unfinished_races(count)

    today_starting_balance = get_today_starting_balance()

    if not current_sporting_index_balance:
        current_sporting_index_balance = df['balance'].values[-1]
    current_betfair_balance = df['betfair_balance'].values[-1]
    in_bet_balance = calc_unfinished_races()
    current_balance = current_sporting_index_balance + current_betfair_balance + in_bet_balance

    total_profit = round(current_balance - STARTING_BALANCE, 2)
    if not today_starting_balance:
        profit_today = 0
    else:
        profit_today = round(current_balance - today_starting_balance, 2)
    if total_profit == 0: total_percentage_profit = 0
    else:
        total_percentage_profit = round(
            (total_profit / STARTING_BALANCE) * 100, 2)

    if profit_today == 0: today_percentage_profit = 0
    else:
        today_percentage_profit = round(
            (profit_today / today_starting_balance) * 100, 2)
    print(
        f'Total profit: £{format(total_profit, ".2f")} ({total_percentage_profit}%)'
    )
    print(
        f'Profit today: £{format(profit_today, ".2f")} ({today_percentage_profit}%)'
    )
    print(
        f'Sporting index balance: £{current_sporting_index_balance} Betfair balance: £{current_betfair_balance} Balance in bets: £{in_bet_balance}'
    )


def plot_bal_time_series_graph():
    import matplotlib.pyplot as plt
    from matplotlib.dates import DateFormatter

    fig, ax = plt.subplots()
    date_fmt = DateFormatter("%d/%m")
    ax.xaxis.set_major_formatter(date_fmt)

    balance = df['balance'] + df['betfair_balance']
    ax.plot(balance, label='Withdrawable')

    for i in range(len(balance)):
        balance[i] += calc_unfinished_races(i)

    ax.plot(balance, label='+ balance in bets')

    expected_return = df['expected_return'] + df['arbritrage_profit']
    expected_return[0] += STARTING_BALANCE
    expected_return.cumsum().plot(label='Expected return')

    fig.autofmt_xdate()
    ax.set_xlabel('Date')
    ax.set_ylabel('Balance (£)')
    ax.legend(loc="best")
    plt.savefig(BALANCE_PNG)
    print('Generated graph at: %s' % BALANCE_PNG)


RETURNS_CSV = os.path.abspath(
    os.path.dirname(__file__) + '/../stats/returns.csv')

BALANCE_PNG = os.path.abspath(
    os.path.dirname(__file__) + '/../stats/balance.png')

df = pd.read_csv(RETURNS_CSV,
                 header=0,
                 parse_dates=[7, 0],
                 index_col=7,
                 date_parser=custom_date_parser,
                 squeeze=True)

try:
    STARTING_BALANCE = df['balance'].values[0] + df['betfair_balance'].values[
        0] + calc_unfinished_races(0)
except IndexError:
    print('No entrys to csv')
    sys.exit()
