import os
import sys
from datetime import datetime
import pandas as pd

from .calculate import custom_date_parser


def calc_unfinished_races(index=-1):
    return df.iloc[index].balance_in_betfair


def get_today_starting_balance():
    try:
        today_first_bet = df.loc[datetime.now().strftime("%Y-%m-%d")].index.values[0]
    except KeyError:
        return None
    count = 0
    for index, _ in df.iterrows():
        if today_first_bet == index:
            break
        count += 1

    return (
        df.loc[datetime.now().strftime("%Y-%m-%d")]["balance"].values[0]
        + df.loc[datetime.now().strftime("%Y-%m-%d")]["betfair_balance"].values[0]
        + calc_unfinished_races(count)
    )


def calculate_returns(current_sporting_index_balance=False):
    today_starting_balance = get_today_starting_balance()

    if not current_sporting_index_balance:
        current_sporting_index_balance = df["balance"].values[-1]
    current_betfair_balance = df["betfair_balance"].values[-1]
    in_bet_balance = calc_unfinished_races()
    current_balance = (
        current_sporting_index_balance + current_betfair_balance + in_bet_balance
    )

    total_profit = round(current_balance - STARTING_BALANCE, 2)
    if not today_starting_balance:
        profit_today = 0
    else:
        profit_today = round(current_balance - today_starting_balance, 2)

    if total_profit == 0:
        total_percentage_profit = 0
    else:
        total_percentage_profit = round((total_profit / STARTING_BALANCE) * 100, 2)

    if profit_today == 0:
        today_percentage_profit = 0
    else:
        today_percentage_profit = round(
            (profit_today / today_starting_balance) * 100, 2
        )
    total_profit = format(total_profit, ".2f")
    profit_today = format(profit_today, ".2f")
    return total_profit, profit_today, total_percentage_profit, today_percentage_profit


def output_profit():
    (
        total_profit,
        profit_today,
        total_percentage_profit,
        today_percentage_profit,
    ) = calculate_returns()
    print(f"Total profit: £{total_profit} ({total_percentage_profit}%)")
    print(f"Profit today: £{profit_today} ({today_percentage_profit}%)")
    print(
        f"Sporting index balance: £{current_sporting_index_balance} Betfair balance: £{current_betfair_balance} Balance in bets: £{in_bet_balance}"
    )


def plot_bal_time_series_graph():
    import matplotlib.pyplot as plt
    from matplotlib.dates import DateFormatter

    fig, ax = plt.subplots()
    date_fmt = DateFormatter("%d/%m")
    ax.xaxis.set_major_formatter(date_fmt)

    balance = df["balance"] + df["betfair_balance"]
    ax.plot(balance, label="Withdrawable")

    for i, _ in enumerate(balance):
        balance[i] += calc_unfinished_races(i)

    ax.plot(balance, label="+ balance in bets")

    expected_return = df["expected_return"] + df["arbritrage_profit"]
    expected_return[0] += STARTING_BALANCE
    expected_return.cumsum().plot(label="Expected return")

    fig.autofmt_xdate()
    ax.set_xlabel("Date")
    ax.set_ylabel("Balance (£)")
    ax.legend(loc="best")

    (
        total_profit,
        profit_today,
        total_percentage_profit,
        today_percentage_profit,
    ) = calculate_returns()
    profit_string = f"Total profit: £{total_profit} ({total_percentage_profit}% \nProfit today: £{profit_today} ({today_percentage_profit}%)"
    plt.annotate(profit_string, xy=(0.05, 0.95), xycoords="axes fraction")

    plt.savefig(BALANCE_PNG)
    print("Generated graph at: %s" % BALANCE_PNG)


RETURNS_CSV = os.path.abspath(os.path.dirname(__file__) + "/../stats/returns.csv")

BALANCE_PNG = os.path.abspath(os.path.dirname(__file__) + "/../stats/balance.png")

df = pd.read_csv(
    RETURNS_CSV,
    header=0,
    parse_dates=[7, 0],
    index_col=7,
    date_parser=custom_date_parser,
    squeeze=True,
)

try:
    STARTING_BALANCE = (
        df["balance"].values[0]
        + df["betfair_balance"].values[0]
        + calc_unfinished_races(0)
    )
except IndexError:
    print("No entrys to csv")
    sys.exit()
