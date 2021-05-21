import os
import math
import difflib
from datetime import datetime
from dotenv import load_dotenv
import numpy as np
from scipy import optimize

BASEDIR = os.path.abspath(os.path.dirname(__file__) + "/../")
load_dotenv(os.path.join(BASEDIR, ".env"))

COMMISSION = float(os.environ.get("COMMISSION"))
PERCENTAGE_BALANCE = float(os.environ.get("PERCENTAGE_BALANCE"))
PERCENTAGE_AVALIABLE = float(os.environ.get("PERCENTAGE_AVALIABLE"))

odds_increments = {
    1: 0.01,
    2: 0.02,
    3: 0.05,
    4: 0.1,
    6: 0.2,
    10: 0.5,
    20: 1,
    30: 2,
    50: 5,
    100: 10,
}


def check_start_time(race, secs):
    seconds_until_race = (race["race_time"] - datetime.now()).total_seconds()
    if seconds_until_race <= secs:
        print("Race too close to start time: %s" % seconds_until_race)
        return False
    return True


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
            return horse, horse

    # sometimes runnerName is 1. horse_name
    for horse in horses:
        if target_horse.lower() in horse.lower():
            return target_horse, horse

    # for horses with punctuation taken out by oddsmonkey
    close_horse = difflib.get_close_matches(target_horse, horses, n=1)[0]
    print("Close horse found: %s (%s)" % (close_horse, target_horse))
    return close_horse, close_horse


def get_min_stake(win_odds, place_odds):
    win_min_stake = 10 / (win_odds - 1)
    win_min_stake = min(win_min_stake, 2)
    place_min_stake = 10 / (place_odds - 1)
    place_min_stake = min(place_min_stake, 2)
    return round(win_min_stake, 2), round(place_min_stake, 2)


def get_max_stake(
    bookie_odds, win_odds, place_odds, win_avaliable, place_avaliable, place_payout
):
    place_payout = 1 / place_payout
    win_stake_ratio = bookie_odds / win_odds
    place_stake_ratio = ((bookie_odds - 1) * place_payout + 1) / place_odds
    total_ratio = 1 + win_stake_ratio + place_stake_ratio
    win_stake_ratio /= total_ratio
    place_stake_ratio /= total_ratio

    # place_avaliable limiting factor
    if place_stake_ratio * place_avaliable < win_stake_ratio * win_avaliable:
        place_stake = place_avaliable
        bookie_stake = place_stake * place_odds / ((bookie_odds - 1) * place_payout + 1)
        win_stake = bookie_stake * bookie_odds / win_odds

    # win_avaliable limiting factor
    else:
        win_stake = win_avaliable
        bookie_stake = win_stake * win_odds / bookie_odds
        place_stake = (
            ((bookie_odds - 1) * place_payout + 1) * bookie_stake
        ) / place_odds
    return bookie_stake, win_stake, place_stake


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
        or (win_stake and win_stake < win_min_stake)
        or (place_stake and place_stake < place_min_stake)
        or (bookie_stake * 2 > bookie_balance)
    ):
        return False
    return True


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


def calculate_expected_return(
    total_balance, win_odds, place_odds, win_profit, place_profit, lose_profit
):
    win_prob = 1 / win_odds
    place_prob = 1 / place_odds - win_prob
    lose_prob = 1 - win_prob - place_prob

    exp_value = (
        win_prob * win_profit + place_prob * place_profit + lose_prob * lose_profit
    ) / total_balance
    exp_growth = (1 + win_profit / total_balance) ** win_prob * (
        1 + place_profit / total_balance
    ) ** place_prob * (1 + lose_profit / total_balance) ** lose_prob - 1
    if isinstance(exp_growth, complex):
        print(
            "ERROR: exp_growth complex - a profit loses more than is in total_balance"
        )
        return 0, 0
    return exp_value, exp_growth, exp_growth * total_balance


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
    except (
        ZeroDivisionError,
        ValueError,
    ):  # if the profit from place is 0 then 0 division
        return 0
    bookie_stake = stake_proportion * balance
    return round(bookie_stake, 2)


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


def calculate_stakes(
    bookie_balance,
    betfair_balance,
    bookie_stake,
    win_stake,
    win_odds,
    place_stake,
    place_odds,
):
    bookie_stake *= PERCENTAGE_AVALIABLE
    win_stake *= PERCENTAGE_AVALIABLE
    place_stake *= PERCENTAGE_AVALIABLE

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

    # create stakes that are PERCENTAGE_BALANCE% the size of our total balance
    min_balance_staked = PERCENTAGE_BALANCE * (betfair_balance + bookie_balance)
    if min_balance_staked > max_stake:
        stake_proporiton = 1
    elif min_balance_staked > min_stake:
        stake_proporiton = min_balance_staked / max_stake
    else:
        # rounds up to reach £2 limit and £10 liability (otherwise can have £1.99)
        bookie_stake = math.ceil(bookie_stake * stake_proporiton * 100) / 100
        win_stake = math.ceil(win_stake * stake_proporiton * 100) / 100
        place_stake = math.ceil(place_stake * stake_proporiton * 100) / 100

    # rounds down when possiblility of stakes exceding balance
    bookie_stake = math.floor(bookie_stake * stake_proporiton * 100) / 100
    win_stake = math.floor(win_stake * stake_proporiton * 100) / 100
    place_stake = math.floor(place_stake * stake_proporiton * 100) / 100

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
            f"win_stake: {win_stake} win_odds: {win_odds} place_stake: {place_stake} place_odds: {place_odds} bookie_stake: {bookie_stake} bookie_balance: {bookie_balance} betfair_balance: {betfair_balance}"
        )
        return False, 0, 0, 0
    return True, bookie_stake, win_stake, place_stake


# N.B bookie_stake is half actual stake
def calculate_stakes_from_profit(
    place_profit,
    lose_profit,
    bookie_stake,
    bookie_odds,
    place_odds,
    place_payout,
):
    place_profit -= bookie_stake * (bookie_odds - 1) / place_payout - bookie_stake
    lose_profit -= -bookie_stake * 2

    place_stake = (place_profit - lose_profit) / (COMMISSION - place_odds)
    win_stake = lose_profit / (1 - COMMISSION) - place_stake
    return round(win_stake, 2), round(place_stake, 2)


def maximize_arb(
    bookie_balance,
    betfair_balance,
    win_odds,
    place_odds,
    win_profit,
    place_profit,
    lose_profit,
    bounds=True,
):
    if bounds:
        bnds = ((0, 1),)
    else:
        bnds = ((None, None),)
    result = optimize.minimize(
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
        bounds=bnds,
    )
    return result.x[0]


def minimize_calculate_profit(
    win_odds,
    place_odds,
    profits,
    betfair_balance,
    place_payout,
):
    def make_minimize(*stakes):
        win_stake, place_stake = stakes[0]
        total_stake = win_stake * (win_odds - 1) + place_stake * (place_odds - 1)
        win_min_stake, place_min_stake = get_min_stake(win_odds, place_odds)
        if total_stake > betfair_balance:
            return total_stake * 100
        if win_stake < win_min_stake:
            win_stake = 0
        elif place_stake < place_min_stake:
            place_stake = 0
        new_profits = calculate_profit(
            0,
            0,
            win_odds,
            win_stake,
            place_odds,
            place_stake,
            place_payout,
            round_profit=False,
        )
        new_profits = np.add(profits, new_profits)
        return -min(new_profits)

    return make_minimize


def minimize_loss(win_odds, place_odds, profits, betfair_balance, place_payout):
    win_min_stake, place_min_stake = get_min_stake(win_odds, place_odds)
    bnds = ((0, betfair_balance), (0, betfair_balance))
    win_stake, place_stake = optimize.differential_evolution(
        minimize_calculate_profit(
            win_odds,
            place_odds,
            profits,
            betfair_balance,
            place_payout,
        ),
        bounds=bnds,
    ).x
    if win_stake < win_min_stake:
        win_stake = 0
    elif place_stake < place_min_stake:
        place_stake = 0
    return round(win_stake, 2), round(place_stake, 2)
