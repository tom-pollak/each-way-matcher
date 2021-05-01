import os
import math
import difflib
from datetime import datetime
from dotenv import load_dotenv
import numpy as np
import pandas as pd
from scipy.optimize import minimize

BASEDIR = os.path.abspath(os.path.dirname(__file__) + "/../")
load_dotenv(os.path.join(BASEDIR, ".env"))

RETURNS_CSV = os.environ.get("RETURNS_CSV")
COMMISSION = float(os.environ.get("COMMISSION"))
PERCENTAGE_BALANCE = float(os.environ.get("PERCENTAGE_BALANCE"))

odds_increments = {
    2: 0.01,
    3: 0.02,
    4: 0.05,
    6: 0.1,
    10: 0.2,
    20: 0.5,
    30: 1,
    50: 2,
    100: 5,
    1000: 10,
}


def custom_date_parser(x):
    if "/" not in x:
        return datetime.strptime(x, "%d %b %H:%M %Y")
    return datetime.strptime(x, "%d/%m/%Y %H:%M:%S")


def check_start_time(race, mins):
    minutes_until_race = (
        datetime.strptime(race["date_of_race"], "%d %b %H:%M %Y") - datetime.now()
    ).total_seconds() / 60
    if minutes_until_race <= mins:
        print("Race too close to start time: %s" % minutes_until_race)
        return False
    return True


def check_repeat_bets(horse_name, date_of_race, venue):
    date_of_race = custom_date_parser(date_of_race)
    df = read_csv()
    if len(df) == 0:
        return [], 1
    horses = df.query(
        "date_of_race == @date_of_race & venue == @venue & (bet_type == 'Punt' | bet_type == 'Arb Punt')"
    )
    horse_races = horses.loc[horses["horse_name"] == horse_name]
    bet_types = horse_races["bet_type"].unique()
    win_odds_proportion = 1 - sum(1 / horses.win_odds)
    return bet_types, win_odds_proportion


def check_odds(race, win_horse_odds, place_horse_odds):
    horse_name, _ = get_valid_horse_name(win_horse_odds.keys(), race["horse_name"])
    try:
        if (
            win_horse_odds[horse_name]["lay_odds_1"] <= race["win_odds"]
            and place_horse_odds[horse_name]["lay_odds_1"] <= race["place_odds"]
            and win_horse_odds[horse_name]["lay_avaliable_1"] >= race["win_stake"]
            and place_horse_odds[horse_name]["lay_avaliable_1"] >= race["place_stake"]
        ):
            return True
        print(
            f"Caught odds changing: {race['win_odds']} -> {win_horse_odds[horse_name]['lay_odds_1'] }"
        )
        print(
            f"\t\t      {race['place_odds']} -> {place_horse_odds[horse_name]['lay_odds_1'] }"
        )
    except KeyError as e:
        print("ERROR scraping betfair %s" % e)
        print(win_horse_odds)
        print(place_horse_odds)
    return False


def read_csv():
    try:
        df = pd.read_csv(
            RETURNS_CSV,
            header=0,
            parse_dates=[0, 1],
            index_col=0,
            date_parser=custom_date_parser,
            squeeze=True,
        )
    except (IndexError, FileNotFoundError):
        return []
    return df


# N.B bookie_stake is half actual stake
def calculate_profit(
    bookie_odds,
    bookie_stake,
    win_odds,
    win_stake,
    place_odds,
    place_stake,
    place_payout,
    round_profit=True,
):
    win_profit = place_profit = lose_profit = 0
    commission_lose = (win_stake + place_stake) * COMMISSION
    commission_place = win_stake * COMMISSION

    place_profit = bookie_stake * (bookie_odds - 1) / place_payout - bookie_stake
    win_profit = bookie_stake * (bookie_odds - 1) + place_profit + bookie_stake
    lose_profit = -bookie_stake * 2

    win_profit -= win_stake * (win_odds - 1) + place_stake * (place_odds - 1)
    place_profit += win_stake - place_stake * (place_odds - 1) - commission_place
    lose_profit += win_stake + place_stake - commission_lose
    if round_profit:
        return round(win_profit, 2), round(place_profit, 2), round(lose_profit, 2)
    return win_profit, place_profit, lose_profit


def get_min_stake(win_odds, place_odds):
    win_min_stake = 10 / (win_odds - 1)
    win_min_stake = min(win_min_stake, 2)
    place_min_stake = 10 / (place_odds - 1)
    place_min_stake = min(place_min_stake, 2)
    return round(win_min_stake, 2), round(place_min_stake, 2)


def check_stakes(
    bookie_balance,
    betfair_balance,
    bookie_stake,
    win_stake,
    win_odds,
    place_stake,
    place_odds,
):
    total_stake = win_stake * (win_odds - 1) + place_stake * (place_odds - 1)
    win_min_stake, place_min_stake = get_min_stake(win_odds, place_odds)
    if (
        (total_stake > betfair_balance)
        or (win_stake < win_min_stake)
        or (place_stake < place_min_stake)
        or (bookie_stake * 2 > bookie_balance)
    ):
        return False
    return True


def kelly_criterion(bookie_odds, win_odds, place_odds, place_payout, balance):
    place_profit = 0.5 * (bookie_odds - 1) / place_payout - 0.5
    win_profit = 0.5 * (bookie_odds - 1) + place_profit + 0.5

    win_prob = 1 / win_odds
    place_prob = 1 / place_odds - win_prob

    A = win_profit * place_profit
    B = (
        (win_prob + place_prob) * win_profit * place_profit
        + win_prob * place_profit
        + place_prob * win_profit
        - win_profit
        - place_profit
    )
    C = (
        win_prob * win_profit + place_prob * place_profit - (1 - win_prob - place_prob)
    )  # Expected profit on 0.5 unit EW bet

    try:
        stake_proportion = (B + math.sqrt(B ** 2 + 4 * A * C)) / (4 * A)
    except ZeroDivisionError:  # if the profit from place is 0 then 0 division
        return 0, 0, "0%"
    bookie_stake = stake_proportion * balance
    return (
        round(bookie_stake, 2),
        round(C * bookie_stake * 2, 2),
        str(round(C * 200, 2)) + "%",
    )


def arb_kelly_criterion(
    proportion,
    total_balance,
    win_profit,
    place_profit,
    lose_profit,
    win_odds,
    place_odds,
):
    win_prob = 1 / win_odds
    place_prob = 1 / place_odds - win_prob
    lose_prob = 1 - win_prob - place_prob

    win_bankroll = total_balance + win_profit * proportion
    place_bankroll = total_balance + place_profit * proportion
    lose_bankroll = total_balance + lose_profit * proportion

    stake_proporiton = -sum(
        [
            p * e
            for p, e in zip(
                [win_prob, place_prob, lose_prob],
                np.log([win_bankroll, place_bankroll, lose_bankroll]),
            )
        ]
    )
    return stake_proporiton


def maximize_arb(
    bookie_balance,
    betfair_balance,
    win_odds,
    place_odds,
    win_profit,
    place_profit,
    lose_profit,
):
    result = minimize(
        arb_kelly_criterion,
        x0=1,
        args=(
            bookie_balance + betfair_balance,
            win_profit,
            place_profit,
            lose_profit,
            win_odds,
            place_odds,
        ),
        bounds=((0, 1),),
    )
    return result.x[0]


def calculate_stakes(
    bookie_balance,
    betfair_balance,
    bookie_stake,
    win_stake,
    win_odds,
    place_stake,
    place_odds,
):
    liabiltity_ratio = 1
    bookie_ratio = bookie_balance / (bookie_stake * 2)

    max_win_liability = (win_odds - 1) * win_stake
    max_place_liability = (place_odds - 1) * place_stake
    total_liability = max_win_liability + max_place_liability

    # ratio of max liability by balance to max possible liability
    if total_liability > betfair_balance:
        liabiltity_ratio = betfair_balance / total_liability
    liabiltity_ratio = min(liabiltity_ratio, bookie_ratio)

    # maximum possible stakes
    bookie_stake *= liabiltity_ratio
    win_stake *= liabiltity_ratio
    place_stake *= liabiltity_ratio

    max_win_liability = (win_odds - 1) * win_stake
    max_place_liability = (place_odds - 1) * place_stake
    max_stake = bookie_stake * 2 + max_win_liability + max_place_liability

    # ratio of minimum allowed stake to maximum stake we can place with current balance
    lay_min_stake_proportion = 0
    bookie_min_stake_proportion = 0.1 / bookie_stake

    if max_win_liability >= 10 and max_place_liability >= 10:
        lay_min_stake_proportion = 10 / min(max_win_liability, max_place_liability)
    if win_stake >= 2 and place_stake >= 2:
        stake_min_stake_proportion = 2 / min(win_stake, place_stake)
        if lay_min_stake_proportion != 0:  # Eligible for > 10 liability
            lay_min_stake_proportion = min(
                lay_min_stake_proportion, stake_min_stake_proportion
            )
        else:
            lay_min_stake_proportion = stake_min_stake_proportion

    if lay_min_stake_proportion == 0:  # max stake not above 2 or liability above 10
        return False, 0, 0, 0

    stake_proporiton = max(bookie_min_stake_proportion, lay_min_stake_proportion)
    min_stake = stake_proporiton * max_stake

    # attempt to create stakes that are 20% the size of our total balance
    min_balance_staked = PERCENTAGE_BALANCE * (betfair_balance + bookie_balance)
    if min_balance_staked > max_stake:
        stake_proporiton = 1
    elif min_balance_staked > min_stake:
        stake_proporiton = min_balance_staked / max_stake

    bookie_stake = math.ceil(bookie_stake * stake_proporiton * 100) / 100
    win_stake = math.ceil(win_stake * stake_proporiton * 100) / 100
    place_stake = math.ceil(place_stake * stake_proporiton * 100) / 100

    # postcondition
    stakes_ok = check_stakes(
        bookie_balance,
        betfair_balance,
        bookie_stake,
        win_stake,
        win_odds,
        place_stake,
        place_odds,
    )
    if not stakes_ok:
        print("Arb stakes not bettable:")
        print(
            f"win_stake: {win_stake} win_odds: {win_odds} place_stake: {place_stake} place_odds: {place_odds} bookie_stake:{bookie_stake} bookie_balance: {bookie_balance} betfair_balance: {betfair_balance}"
        )
        return False, 0, 0, 0

    return True, bookie_stake, win_stake, place_stake


def calculate_expected_return(
    total_balance, win_odds, place_odds, win_profit, place_profit, lose_profit
):
    win_prob = 1 / win_odds
    place_prob = 1 / place_odds - win_prob
    lose_prob = 1 - win_prob - place_prob

    exp_growth = (1 + win_profit / total_balance) ** win_prob * (
        1 + place_profit / total_balance
    ) ** place_prob * (1 + lose_profit / total_balance) ** lose_prob - 1
    exp_value = (
        win_prob * win_profit + place_prob * place_profit + lose_prob * lose_profit
    )
    if isinstance(exp_growth, complex):
        print(
            "ERROR: exp_growth complex - a profit loses more than is in total_balance"
        )
        return exp_value, 0, 0
    return exp_value, exp_growth, exp_growth * total_balance


def round_odd(odd):
    if odd is None:
        return None
    for price in odds_increments:
        if odd > price:
            odd = odds_increments[price] * round(odd / odds_increments[price])

    return round(odd, 2)


def get_next_odd_increment(odd):
    for price in odds_increments:
        if odd < price:
            return round(odd + odds_increments[price], 2)
    return None


def get_valid_horse_name(horses, target_horse):
    for horse in horses:
        if horse.lower() == target_horse.lower():
            return horse, True

    # sometimes runnerName is 1. horse_name
    for horse in horses["runners"]:
        if target_horse.lower() in horse.lower():
            return horse, False

    # for horses with punctuation taken out by oddsmonkey
    close_horse = difflib.get_close_matches(target_horse, horses, n=1)[0]
    print("Close horse found: %s (%s)" % (close_horse, target_horse))
    return close_horse, True


def minimize_calculate_profit(
    win_odds,
    place_odds,
    profits,
    win_min_stake,
    place_min_stake,
    betfair_balance,
):
    def make_minimize(stakes):
        if stakes[0] < win_min_stake:
            stakes[0] = 0
        if stakes[1] < place_min_stake:
            stakes[1] = 0
        if not check_stakes(
            0,
            betfair_balance,
            0,
            stakes[0],
            win_odds,
            stakes[1],
            place_odds,
        ):
            return (stakes[0] + stakes[1]) * 1000

        min_profits = calculate_profit(
            0,
            0,
            win_odds,
            stakes[0],
            place_odds,
            stakes[1],
            5,
            round_profit=False,
        )
        min_profits = np.add(profits, min_profits)
        return -min(min_profits)

    return make_minimize


def minimize_loss(
    win_odds,
    place_odds,
    profits,
    betfair_balance,
):
    win_min_stake, place_min_stake = get_min_stake(win_odds, place_odds)
    x0 = (win_min_stake, place_min_stake)
    bnds = ((0, None), (0, None))
    win_stake, place_stake = minimize(
        minimize_calculate_profit(
            win_odds,
            place_odds,
            profits,
            win_min_stake,
            place_min_stake,
            betfair_balance,
        ),
        x0=x0,
        bounds=bnds,
    ).x
    if win_stake < win_min_stake:
        win_stake = None
    if place_stake < place_min_stake:
        place_stake = None
    return round(win_stake, 2), round(place_stake, 2)
