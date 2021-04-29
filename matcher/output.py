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
    print(
        f"\nNo Lay bet made ({datetime.now().strftime('%H:%M:%S')}): {race['horse_name']} - {race['bookie_odds']}"
    )
    print(f"\t{race['date_of_race']} - {race['venue']}")
    print(f"\tLay win: {race['win_odds']} Lay place: {race['place_odds']}")
    try:
        print(
            f"\tExpected value: {race['exp_value']}, Expected return: £{format(race['exp_return'], '.2f')}, Expected Growth: {round(race['exp_growth'], 2 * 100)}"
        )
    except KeyError:
        print("Key Error in output_race")
    print(
        f"\tCurrent balance: £{format(race['bookie_balance'], '.2f')}, stake: £{format(race['bookie_stake'], '.2f')}\n"
    )


def output_lay_ew(race):
    print(
        f"\n{race['bet_type']} bet made ({datetime.now().strftime('%H:%M:%S')}): {race['horse_name']} - profit: £{format(race['exp_return'], '.2f')}"
    )
    print(f"\t{race['date_of_race']} - {race['venue']}")
    print(
        f"\tBack bookie: {race['bookie_odds']} - £{format(race['bookie_stake'], '.2f')} Lay win: {race['win_odds']} - £{format(race['win_stake'], '.2f')} Lay place: {race['place_odds']} - £{format(race['place_stake'], '.2f')}"
    )
    print(
        f"\tWin profit: £{format(race['win_profit'], '.2f')} Place profit: £{format(race['place_profit'], '.2f')} Lose profit: £{format(race['lose_profit'], '.2f')}"
    )
    print(
        f"Expected Value: {race['exp_value']}, Expected Growth: {round(race['exp_growth'], 2 * 100)}%"
    )
    print(
        f"Current balance: £{format(race['bookie_balance'], '.2f')}, betfair balance: £{format(race['betfair_balance'], '.2f')}\n"
    )


def update_csv_sporting_index(race):
    race["win_stake"] = race["place_stake"] = 0
    csv_columns = [
        "current_time",
        "date_of_race",
        "venue",
        "horse_name",
        "exp_value",
        "exp_growth",
        "exp_return",
        "bookie_stake",
        "bookie_odds",
        "win_stake",
        "win_odds",
        "place_stake",
        "place_odds",
        "bookie_balance",
        "betfair_balance",
        "betfair_in_bet_balance",
        "win_profit",
        "place_profit",
        "lose_profit",
        "bet_type",
        "place_payout",
    ]
    with open(RETURNS_CSV, "a+", newline="") as returns_csv:
        csv_writer = DictWriter(
            returns_csv, fieldnames=csv_columns, extrasaction="ignore"
        )
        csv_writer.writerow(race)


def update_csv_betfair(race):
    csv_columns = [
        "current_time",
        "date_of_race",
        "venue",
        "horse_name",
        "exp_value",
        "exp_growth",
        "exp_return",
        "bookie_stake",
        "bookie_odds",
        "win_stake",
        "win_odds",
        "place_stake",
        "place_odds",
        "bookie_balance",
        "betfair_balance",
        "betfair_in_bet_balance",
        "win_profit",
        "place_profit",
        "lose_profit",
        "bet_type",
        "place_payout",
    ]
    with open(RETURNS_CSV, "a+", newline="") as returns_csv:
        csv_writer = DictWriter(
            returns_csv, fieldnames=csv_columns, extrasaction="ignore"
        )
        csv_writer.writerow(race)
