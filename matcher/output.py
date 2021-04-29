import os
from time import time
from datetime import datetime
from dotenv import load_dotenv
from csv import DictWriter

import matcher.sites.betfair as betfair
import matcher.sites.sporting_index as sporting_index


BASEDIR = os.path.abspath(os.path.dirname(__file__) + "/../")
load_dotenv(os.path.join(BASEDIR, ".env"))
RETURNS_CSV = os.environ.get("RETURNS_CSV")


def show_info(count, START_TIME):
    def convert_time(time_secs):
        hours = int(time_secs // 60 ** 2)
        mins = int(time_secs // 60 - hours * 60)
        secs = round(time_secs - (hours * 60 * 60) - (mins * 60))
        return f"{hours:02}:{mins:02}:{secs:02}"

    diff = time() - START_TIME
    time_alive = convert_time(diff)

    print(f"Time is: {datetime.now().strftime('%H:%M:%S')}\tTime alive: {time_alive}")
    print(f"Refreshes: {count}")
    if datetime.now().hour >= 18:
        print("\nFinished matching today")
        print("---------------------------------------------")
        raise KeyboardInterrupt


def output_race(driver, race):
    balance = sporting_index.get_balance(driver)
    print(
        f"\nNo Lay bet made ({datetime.now().strftime('%H:%M:%S')}): {race['horse_name']} - {race['bookie_odds']}"
    )
    print(f"\t{race['date_of_race']} - {race['venue']}")
    print(f"\tLay win: {race['win_odds']} Lay place: {race['place_odds']}")
    try:
        print(
            f"\tExpected value: {race['expected_value']}, Expected return: £{format(race['expected_return'], '.2f')}"
        )
    except KeyError:
        print("Key Error in output_race")
    print(
        f"\tCurrent balance: £{format(balance, '.2f')}, stake: £{format(race['bookie_stake'], '.2f')}\n"
    )


def output_lay_ew(race, profit):
    print(
        f"\n{race["bet_type"]} bet made ({datetime.now().strftime('%H:%M:%S')}): {race['horse_name']} - profit: £{format(profit, '.2f')}"
    )
    print(f"\t{race['date_of_race']} - {race['venue']}")
    print(
        f"\tBack bookie: {race['bookie_odds']} - £{format(race['bookie_stake'], '.2f')} Lay win: {race['win_odds']} - £{format(race['win_stake'], '.2f')} Lay place: {race['place_odds']} - £{format(race['place_stake'], '.2f')}"
    )
    print(
        f"\tWin profit: £{format(race['win_profit'], '.2f')} Place profit: £{format(race['place_profit'], '.2f')} Lose profit: £{format(race['lose_profit'], '.2f')}"
    )
    print(
        f"Current balance: £{format(race['balance'], '.2f')}, betfair balance: £{format(race['betfair_balance'], '.2f')}\n"
    )


def update_csv_sporting_index(driver, race):
    race["arbritrage_profit"] = 0
    race["balance"] = sporting_index.get_balance(driver)
    race["betfair_balance"] = betfair.get_balance()
    race["balance_in_betfair"] = betfair.get_balance_in_bets()
    csv_columns = [
        "date_of_race",
        "horse_name",
        "bookie_odds",
        "venue",
        "bookie_stake",
        "balance",
        "rating",
        "expected_value",
        "expected_return",
        "win_stake",
        "place_stake",
        "win_odds",
        "place_odds",
        "betfair_balance",
        "max_profit",
        "bet_type",
        "arbritrage_profit",
        "place_payout",
        "balance_in_betfair",
        "current_time",
    ]
    with open(RETURNS_CSV, "a+", newline="") as returns_csv:
        csv_writer = DictWriter(
            returns_csv, fieldnames=csv_columns, extrasaction="ignore"
        )
        csv_writer.writerow(race)


def update_csv_betfair(race, arbritrage_profit):
    race["arbritrage_profit"] = arbritrage_profit
    race["expected_value"] = race["expected_return"] = 0
    race["balance_in_betfair"] = betfair.get_balance_in_bets()
    csv_columns = [
        "date_of_race",
        "horse_name",
        "bookie_odds",
        "venue",
        "bookie_stake",
        "balance",
        "rating",
        "expected_value",
        "expected_return",
        "win_stake",
        "place_stake",
        "win_odds",
        "place_odds",
        "betfair_balance",
        "max_profit",
        "bet_type",
        "arbritrage_profit",
        "place_payout",
        "balance_in_betfair",
        "current_time",
    ]
    with open(RETURNS_CSV, "a+", newline="") as returns_csv:
        csv_writer = DictWriter(
            returns_csv, fieldnames=csv_columns, extrasaction="ignore"
        )
        csv_writer.writerow(race)
