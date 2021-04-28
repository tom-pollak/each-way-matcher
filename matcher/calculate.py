import os
import math
from datetime import datetime
from time import strptime
from dotenv import load_dotenv
import numpy as np
import pandas as pd
from scipy.optimize import minimize

BASEDIR = os.path.abspath(os.path.dirname(__file__) + "/../")
load_dotenv(os.path.join(BASEDIR, ".env"))

MIN_PERCENTAGE_BALANCE = 0
RETURNS_CSV = os.environ.get("RETURNS_CSV")
COMMISSION = float(os.environ.get("COMMISSION"))

price_increments = {
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
        return datetime(*(strptime(x, "%d %b %H:%M %Y")[0:6]))
    return datetime(*(strptime(x, "%d/%m/%Y %H:%M:%S")[0:6]))


def check_repeat_bets(horse_name, date_of_race, venue):
    date_of_race = custom_date_parser(date_of_race)
    try:
        df = pd.read_csv(
            RETURNS_CSV,
            header=0,
            parse_dates=[19, 0],
            index_col=19,
            date_parser=custom_date_parser,
            squeeze=True,
        )
    except IndexError:
        return False
    mask = (
        (df["horse_name"] == horse_name)
        & (df["date_of_race"] == date_of_race)
        & (df["venue"] == venue)
        & (df["is_lay"] == False)
    )
    if len(df.loc[mask]) == 0:
        return True
    if len(df.loc[mask]) > 1:
        print("ERROR more than one race matched")
        print(df.loc[mask])
    return False


def check_stakes(
    bookie_balance,
    betfair_balance,
    bookie_stake,
    win_stake,
    win_odds,
    place_stake,
    place_odds,
):
    if (
        (win_stake * (win_odds - 1) + place_stake * (place_odds - 1) > betfair_balance)
        or (win_stake < 2 and win_stake * (win_odds - 1) < 10)
        or (place_stake < 2 and place_stake * (place_odds - 1) < 10)
        or (bookie_balance is not None and bookie_stake * 2 > bookie_balance)
    ):
        print("Arb stakes not bettable:")
        print(
            f"win_stake: {win_stake} win_odds: {win_odds} place_stake: {place_stake} place_odds: {place_odds} bookie_stake:{bookie_stake} bookie_balance: {bookie_balance} betfair_balance: {betfair_balance}"
        )
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
    proportion, win_profit, place_profit, lose_profit, win_odds, place_odds
):
    win_prob = 1 / win_odds
    place_prob = 1 / place_odds - win_prob
    lose_prob = 1 - win_prob - place_prob

    try:
        stake_proporiton = (
            win_prob * math.log10(1 + win_profit * proportion)
            + place_prob * math.log10(1 + place_profit * proportion)
            + lose_prob * math.log10(1 + lose_profit * proportion)
        )
    except ValueError:
        return 9999
    return -stake_proporiton


def maximize_arb(win_odds, place_odds, win_profit, place_profit, lose_profit):
    result = minimize(
        arb_kelly_criterion,
        0,
        args=(win_profit, place_profit, lose_profit, win_odds, place_odds),
        bounds=((0, 1),),
    )
    if result.fun == 9999:
        return 0
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
    min_balance_staked = MIN_PERCENTAGE_BALANCE * (betfair_balance + bookie_balance)
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
        return False, 0, 0, 0

    return True, bookie_stake, win_stake, place_stake


def round_stake(odd):
    for price in price_increments:
        if odd < price:
            return round(
                round(odd / price_increments[price]) * price_increments[price], 2
            )
    return odd


def get_next_odd_increment(odd):
    for price in price_increments:
        if odd < price:
            return round(odd + price_increments[price], 2)
    return None


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

    if bookie_odds is not None and bookie_stake is not None:
        place_profit = bookie_stake * (bookie_odds - 1) / place_payout - bookie_stake
        win_profit = bookie_stake * (bookie_odds - 1) + place_profit + bookie_stake
        lose_profit = -bookie_stake * 2

    win_profit -= win_stake * (win_odds - 1) + place_stake * (place_odds - 1)
    place_profit += win_stake - place_stake * (place_odds - 1) - commission_place
    lose_profit += win_stake + place_stake - commission_lose
    if round_profit:
        return round(win_profit, 2), round(place_profit, 2), round(lose_profit, 2)
    return win_profit, place_profit, lose_profit


def check_odds_changes(race, win_horse_odds, place_horse_odds):
    try:
        if not (
            win_horse_odds[race["horse_name"]]["lay_odds_1"] > race["win_odds"]
            and place_horse_odds[race["horse_name"]]["lay_odds_1"] > race["place_odds"]
            and win_horse_odds[race["horse_name"]]["lay_avaliable_1"]
            < race["win_stake"]
            and place_horse_odds[race["horse_name"]]["lay_avaliable_1"]
            < race["place_stake"]
        ):
            return False
        print(
            f"Caught odds changing: {race['win_odds']} -> {win_horse_odds[race['horse_name']]['lay_odds_1'] }"
        )
        print(
            f"\t\t      {race['place_odds']} -> {place_horse_odds[race['horse_name']]['lay_odds_1'] }"
        )
    except KeyError:
        print("ERROR scraping betfair")
        print(win_horse_odds)
        print(place_horse_odds)
    return True


def minimize_calculate_profits(
    bookie_odds,
    bookie_stake,
    win_odds,
    place_odds,
    place_payout,
    win_stake,
    place_stake,
    profits,
):
    def make_minimize(stakes):
        w_stake = stakes[0] + win_stake
        p_stake = stakes[1] + place_stake

        min_profits = calculate_profit(
            bookie_odds,
            bookie_stake,
            win_odds,
            w_stake,
            place_odds,
            p_stake,
            place_payout,
            round_profit=False,
        )
        min_profits = np.add(profits, min_profits)
        return -min(min_profits)

    return make_minimize


def minimize_loss(
    bookie_odds,
    bookie_stake,
    win_odds,
    place_odds,
    place_payout,
    win_stake,
    place_stake,
    profits,
):
    x0 = [0 for x in [win_stake, place_stake]]
    bnds = [(0, None) for x in [win_stake, place_stake]]
    win_stake, place_stake = minimize(
        minimize_calculate_profits(
            bookie_odds,
            bookie_stake,
            win_odds,
            place_odds,
            place_payout,
            win_stake,
            place_stake,
            profits,
        ),
        x0=x0,
        bounds=bnds,
    ).x
    return round_stake(win_stake), round_stake(place_stake)
