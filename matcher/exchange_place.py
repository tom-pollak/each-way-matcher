from datetime import datetime
import matcher.sites.betfair as betfair
from matcher.exceptions import MatcherError
import pandas as pd

PLACES = 4
COMMISSION = 0.02

idx = pd.IndexSlice


def normalize_probs(probs, odds=True):
    if odds:
        probs = [1 / x for x in probs]
    total_prob = sum(probs)
    if total_prob <= 0:
        print("Invalid probabilities: Total probability = %s" % total_prob)
        return None
    if total_prob != 1:
        # print("Normalizing prob by a factor of %s" % total_prob)
        probs = map(lambda x: x / total_prob, probs)
    return list(probs)


def calc_places_prob(
    horses,  # horse place probabilities
    cur_neg_prob=1,  # total amount of prob left for the rest of the horses in solution
    cur_adj_factor=1,  # probability adjustment using amount of prob left
    included_r=None,  # checks whether already included a runner in race solution
    recursion_level=0,
):
    """Recursively iterates through every horse placement position and calculates probability positions given the positions already allocated (if that makes any sense)"""
    if included_r is None:
        included_r = []
    recursion_level += 1
    for horse, probabilities in horses.items():
        prob = probabilities[0]
        if horse in included_r:
            continue
        # print(horse, included_r)

        if recursion_level > 1:
            horses[horse][recursion_level - 1] += prob * cur_adj_factor

        if recursion_level < RELEVANT_PLACES:
            neg_prob = cur_neg_prob - prob  # previous neg probs - cur prob
            adj_factor = cur_adj_factor * prob / neg_prob
            # print(adj_factor, neg_prob)
            included_r.append(horse)
            horses = calc_places_prob(
                horses, neg_prob, adj_factor, included_r, recursion_level
            )
            included_r.remove(horse)
    return horses


def calc_horse_place_probs(horses):
    probs = normalize_probs(list(horses.values()))
    place_probs_r = [[0 for _ in horses] for _ in horses]
    for i, item in enumerate(place_probs_r):
        item[0] = list(probs)[i]

    horses = dict(zip(horses.keys(), place_probs_r))
    return calc_places_prob(horses)


def get_betfair_odds(races_df, odds_df):
    for index, race in (
        races_df.query("time > @datetime.now()")
        .sort_values("time", ascending=True)
        .sort_index(level=1)
        .iterrows()
    ):
        horses_win = {}
        horses_place = {}
        for name, selection_id in odds_df.loc[index, "Betfair Exchange Win"][
            "selection_id"
        ].items():
            try:
                horses_win[name] = betfair.get_odds(race["win_market_id"], selection_id)
                horses_place[name] = betfair.get_odds(
                    race["place_market_id"], selection_id
                )
            except (MatcherError, ValueError):
                odds_df.drop((index[0], index[1], name), inplace=True)
                continue
        update_odds_df(odds_df, index[0], index[1], horses_win, "Betfair Exchange Win")
        update_odds_df(
            odds_df, index[0], index[1], horses_place, "Betfair Exchange Place"
        )


def run_exchange_bet():
    betfair.get_daily_races()
