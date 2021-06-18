import os
from datetime import datetime
from dotenv import load_dotenv
import pandas as pd

from .race_results import get_position


BASEDIR = os.path.abspath(os.path.dirname(__file__) + "/../")
load_dotenv(os.path.join(BASEDIR, ".env"))

RETURNS_CSV = os.environ.get("RETURNS_CSV")
BALANCE_PNG = os.path.join(BASEDIR, os.environ.get("BALANCE_PNG"))


def read_csv():
    try:
        df = pd.read_csv(
            RETURNS_CSV,
            header=0,
            parse_dates=[0, 1],
            index_col=0,
            squeeze=True,
        )
    except (IndexError, FileNotFoundError):
        df = []
    return df


def check_repeat_bets(horse_name, race_time, venue):
    df = read_csv()
    if len(df) == 0:
        return [], 1, (0, 0, 0)
    horses = df.query(
        "race_time == @race_time & venue == @venue & (bet_type == 'Punt' | bet_type == 'Lay Punt')"
    )
    win_odds_proportion = 1 - sum(1 / horses.loc[horses["bet_type"] == "Punt"].win_odds)

    horse_races = horses.loc[horses["horse_name"] == horse_name]
    profits = horse_races.loc[
        horse_races["bet_type"] == "Lay Punt",
        ["win_profit", "place_profit", "lose_profit"],
    ].sum()
    bet_types = horse_races["bet_type"].unique()
    if win_odds_proportion > 1:
        print(f"win_odds_proportion {win_odds_proportion}")
        win_odds_proportion = 1
    return bet_types, win_odds_proportion, tuple(profits)


def calc_unfinished_races(index=-1):
    df = read_csv()
    try:
        mask = (df["race_time"] >= df.index.values[index]) & (
            df.index <= df.index.values[index]
        )
        races = df.loc[mask]
        in_bet_balance = (
            sum(races["bookie_stake"] * 2) + df.iloc[index]["betfair_exposure"]
        )
    except IndexError:
        return 0
    return round(in_bet_balance, 2)


def update_horse_places():
    df = read_csv()
    no_pos_rows = df[df["position"].isna()]
    for index, race in no_pos_rows.iterrows():
        pos = get_position(race.venue, race.race_time, race.horse_name)
        if pos is not None:
            df.at[index, "position"] = pos
    df.to_csv(RETURNS_CSV)


def get_today_starting_balance():
    df = read_csv()
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
    df = read_csv()
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
    df = read_csv()
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
    print(
        f"""Total profit: £{total_profit} ({total_percentage_profit}%)
Profit today: £{profit_today} ({today_percentage_profit}%)
Sporting Index balance: £{current_sporting_index_balance} Betfair balance: £{current_betfair_balance} Balance in bets: £{in_bet_balance}\
    """
    )


def plot_bal_time_series_graph():
    def create_return_rows(
        win_profit, place_profit, lose_profit, bet_type, places_paid, position
    ):
        punt_return = arb_return = 0
        if position == 1:
            profit = win_profit
        elif position <= places_paid:
            profit = place_profit
        else:
            profit = lose_profit

        if bet_type == "Punt":
            punt_return = profit
        else:
            arb_return = profit

        return pd.Series(data={"punt_return": punt_return, "arb_return": arb_return})

    import matplotlib.pyplot as plt
    from matplotlib.dates import DateFormatter

    df = read_csv()
    fig, ax = plt.subplots()
    date_fmt = DateFormatter("%d/%m")
    ax.xaxis.set_major_formatter(date_fmt)

    balance = df["bookie_balance"] + df["betfair_balance"]
    df[["punt_return", "arb_return"]] = df.apply(
        lambda x: create_return_rows(
            x["win_profit"],
            x["place_profit"],
            x["lose_profit"],
            x["bet_type"],
            x["places_paid"],
            x["position"],
        ),
        axis=1,
    )

    for i, _ in enumerate(balance):
        balance[i] += calc_unfinished_races(i)

    ax.plot(balance, "g", label="Profit")

    i = df.iloc[[0]].index
    df.loc[i, "exp_return"] += STARTING_BALANCE
    df.loc[i, "punt_return"] += STARTING_BALANCE
    df.loc[i, "arb_return"] += STARTING_BALANCE
    df["punt_return"] = df["punt_return"].cumsum(skipna=False)
    df["arb_return"] = df["arb_return"].cumsum(skipna=False)
    df.fillna(method="ffill", inplace=True)
    df["exp_return"].cumsum().plot(color="r", label="Expected return")
    df.set_index("race_time")["punt_return"].plot(color="b", label="Punt return")
    df.set_index("race_time")["arb_return"].plot(label="Arb return")

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


_df = read_csv()
if len(_df) == 0:
    STARTING_BALANCE = 0
else:
    STARTING_BALANCE = (
        _df["bookie_balance"].values[0]
        + _df["betfair_balance"].values[0]
        + calc_unfinished_races(0)
    )
