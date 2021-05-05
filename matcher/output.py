import os
from time import time
from datetime import datetime
from dotenv import load_dotenv
from csv import DictWriter

from matcher.stats import calc_unfinished_races, output_profit


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
        output_profit()
        raise KeyboardInterrupt


def output_punt(race):
    print(
        f"""
    No Lay bet made ({datetime.now().strftime('%H:%M:%S')}): {race['horse_name']} - {race['bookie_odds']} (£{format(race['exp_return'], '.2f')})
        {race['date_of_race']} - {race['venue']}
        Win odds: {race['win_odds']} Place odds: {race['place_odds']}
        Expected value: {round(race['exp_value'] * 100, 2)}%, Expected Growth: {round(race['exp_growth'] * 100, 2)}%
        Sporting Index balance: £{format(race['bookie_balance'], '.2f')}, stake: £{format(race['bookie_stake'], '.2f')}
    """
    )


def ouput_lay(race):
    print(
        f"""
    {race['bet_type']} bet made ({datetime.now().strftime('%H:%M:%S')}): {race['horse_name']} (£{format(race['exp_return'], '.2f')})
        {race['date_of_race']} - {race['venue']}
        Bookie odds: {race['bookie_odds']} - £{format(race['bookie_stake'], '.2f')} Lay win: {race['win_odds']} - £{format(race['win_stake'], '.2f')} Lay place: {race['place_odds']} - £{format(race['place_stake'], '.2f')}
        Win profit: £{format(race['win_profit'], '.2f')} Place profit: £{format(race['place_profit'], '.2f')} Lose profit: £{format(race['lose_profit'], '.2f')}
        Expected Value: {round(race['exp_value'] * 100, 2)}%, Expected Growth: {round(race['exp_growth'] * 100, 2)}%
        Sporting Index balance: £{format(race['bookie_balance'], '.2f')}, Betfair balance: £{format(race['betfair_balance'], '.2f')} In bet balance: {format(calc_unfinished_races(), '.2f')}
    """
    )


def update_csv(race):
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
