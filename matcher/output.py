import os
from time import time
from datetime import datetime
from dotenv import load_dotenv
from csv import DictWriter

from matcher.stats import calc_unfinished_races


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

    print(f"\nTime is: {datetime.now().strftime('%H:%M:%S')}\tTime alive: {time_alive}")
    print(f"Refreshes: {count}")
    if datetime.now().hour >= 19:
        print("\nFinished matching today")
        print("---------------------------------------------")
        raise KeyboardInterrupt


def alert_low_funds(race):
    total_balance = (
        race["bookie_balance"] + race["betfair_balance"] + calc_unfinished_races()
    )
    alerted = False
    if race["bookie_balance"] < 0.1 * total_balance:
        print(f"Bookie balance low: £{format(race['bookie_balance'], '.2f')}")
        alerted = True
    if race["betfair_balance"] < 0.2 * total_balance:
        print(f"Betfair balance low: £{format(race['betfair_balance'], '.2f')}")
        alerted = True
    if alerted:
        print()


def output_punt(race):
    print(
        f"""
Punt bet made ({datetime.now().strftime('%H:%M:%S')}): {race['horse_name']} - {race['bookie_odds']}
    {race['race_time']} - {race['venue']}
    Win odds: {race['win_odds']} Place odds: {race['place_odds']}
    Expected Value: {round(race['exp_value'] * 100, 2)}% Expected Growth: {round(race['exp_growth'] * 100, 2)}% (£{format(race['exp_return'], '.2f')})
    Sporting Index balance: £{format(race['bookie_balance'], '.2f')}, Stake: £{format(race['bookie_stake'], '.2f')}"""
    )


def ouput_lay(race):
    print(
        f"""
{race['bet_type']} bet made ({datetime.now().strftime('%H:%M:%S')}): {race['horse_name']}
    {race['race_time']} - {race['venue']}
    Bookie odds: {race['bookie_odds']} - £{format(race['bookie_stake'], '.2f')} Lay win: {race['win_odds']} - £{format(race['win_stake'], '.2f')} Lay place: {race['place_odds']} - £{format(race['place_stake'], '.2f')}
    Win profit: £{format(race['win_profit'], '.2f')} Place profit: £{format(race['place_profit'], '.2f')} Lose profit: £{format(race['lose_profit'], '.2f')}
    Expected Value: {round(race['exp_value'] * 100, 2)}% Expected Growth: {round(race['exp_growth'] * 100, 2)}% (£{format(race['exp_return'], '.2f')})
    Sporting Index balance: £{format(race['bookie_balance'], '.2f')}, Betfair balance: £{format(race['betfair_balance'], '.2f')} In bet balance: {format(calc_unfinished_races(), '.2f')}"""
    )


def update_csv(race):
    csv_columns = [
        "current_time",
        "race_time",
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
        "betfair_exposure",
        "win_profit",
        "place_profit",
        "lose_profit",
        "bet_type",
        "place_payout",
        "places_paid",
        "postion",
    ]
    with open(RETURNS_CSV, "a+", newline="") as returns_csv:
        csv_writer = DictWriter(
            returns_csv, fieldnames=csv_columns, extrasaction="ignore"
        )
        csv_writer.writerow(race)
