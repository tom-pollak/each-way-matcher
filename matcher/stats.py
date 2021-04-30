import os
from datetime import datetime
from dotenv import load_dotenv

from .exceptions import MatcherError
from .calculate import read_csv


BASEDIR = os.path.abspath(os.path.dirname(__file__) + "/../")
load_dotenv(os.path.join(BASEDIR, ".env"))

BALANCE_PNG = os.path.join(BASEDIR, os.environ.get("BALANCE_PNG"))


def calc_unfinished_races(index=-1):
    in_bet_balance = 0
    mask = (df["date_of_race"] >= df.index.values[index]) & (
        df.index <= df.index.values[index]
    )
    races = df.loc[mask]
    for _, row in races.iterrows():
        in_bet_balance += row["bookie_stake"] * 2
    return round(in_bet_balance + df.iloc[index]["betfair_in_bet_balance"], 2)


def get_today_starting_balance():
    try:
        today_first_bet = df.loc[datetime.now().strftime("%Y-%m-%d")].index.values[0]
    except KeyError:
        return None
    num_races = df[:today_first_bet].shape[0] - 1

    return (
        df.loc[datetime.now().strftime("%Y-%m-%d")]["bookie_balance"].values[0]
        + df.loc[datetime.now().strftime("%Y-%m-%d")]["betfair_balance"].values[0]
        + calc_unfinished_races(num_races)
    )


def calculate_returns():
    if len(df) == 0:
        return 0, 0, 0, 0
    today_starting_balance = get_today_starting_balance()

    current_sporting_index_balance = df["bookie_balance"].values[-1]
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
    if len(df) == 0:
        current_sporting_index_balance = 0
        current_betfair_balance = 0
        in_bet_balance = 0
    else:
        current_sporting_index_balance = df["bookie_balance"].values[-1]
        current_betfair_balance = df["betfair_balance"].values[-1]
        in_bet_balance = format(calc_unfinished_races(), ".2f")
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

    balance = df["bookie_balance"] + df["betfair_balance"]
    # ax.plot(balance, label="Withdrawable")

    for i, _ in enumerate(balance):
        balance[i] += calc_unfinished_races(i)

    ax.plot(balance, "g", label="Profit")

    df["exp_return"][0] += STARTING_BALANCE
    df["exp_return"].cumsum().plot(color="r", label="Minimum expected return")

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
    profit_string = f"Total profit: £{total_profit} ({total_percentage_profit}%) \nProfit today: £{profit_today} ({today_percentage_profit}%)"
    plt.gcf().text(0.55, 0.92, profit_string)

    plt.savefig(BALANCE_PNG)
    # print("Generated graph at: %s" % BALANCE_PNG)


df = read_csv()
if len(df) == 0:
    print("returns.csv is empty/ not found!")

if len(df) == 0:
    STARTING_BALANCE = 0
else:
    STARTING_BALANCE = (
        df["bookie_balance"].values[0]
        + df["betfair_balance"].values[0]
        + calc_unfinished_races(0)
    )
