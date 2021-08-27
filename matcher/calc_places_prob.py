import matcher.sites.betfair as betfair

EXTRA_PLACE_POSITION = 4
RELEVANT_PLACES = 8

# horses = {
#     "horse1": 5.03,
#     "horse2": 28.17,
#     "horse3": 28.34,
#     "horse4": 8,
#     "horse5": 6.76,
#     "horse6": 10,
#     "horse7": 4.61,
#     "horse8": 77.62,
#     "horse9": 17.22,
#     "horse10": 16.94,
#     "horse11": 58.24,
# }
#
# places = {
#     "horse1": 1.89,
#     "horse2": 7.09,
#     "horse3": 7.2,
#     "horse4": 2.75,
#     "horse5": 2.47,
#     "horse6": 2.98,
#     "horse7": 1.97,
#     "horse8": 15,
#     "horse9": 4.7,
#     "horse10": 4.6,
#     "horse11": 13,
# }

horses = {
    "horse1": 7.6,
    "horse2": 4.6,
    "horse3": 8.2,
    "horse4": 8,
    "horse5": 10,
    "horse6": 6.6,
    "horse7": 10,
    "horse8": 13.5,
    "horse9": 40,
}

places_back = {
    "horse1": [3.4, 2.4, 1.62],
    "horse2": [2.3, 1.86, 1.39],
    "horse3": [3.9, 2.58, 1.78],
    "horse4": [3.65, 2.5, 1.92],
    "horse5": [4.2, 2.84, 1.7],
    "horse6": [3.3, 2.28, 1.74],
    "horse7": [4.6, 3.05, 2.08],
    "horse8": [3.9, 3.4, 2.18],
    "horse9": [10, 6.4, 2.78],
}

places_lay = {
    "horse1": [7, 3.2, 2.54],
    "horse2": [2.74, 2.08, 1.94],
    "horse3": [7, 3, 2.7],
    "horse4": [7.2, 3.05, 21],
    "horse5": [11, 3.5, 2.9],
    "horse6": [6, 2.58, 2.52],
    "horse7": [11, 5.6, 3.55],
    "horse8": [18, 9.8, 4.9],
    "horse9": [90, 7.8, 20],
}


def normalize_probs(probs, odds=True):
    if odds:
        probs = [1 / x for x in probs]
    total_prob = sum(probs)
    if total_prob <= 0:
        print("Invalid probabilities: Total probability = %s" % total_prob)
        return None
    if total_prob != 1:
        print("Normalizing prob by a factor of %s" % total_prob)
        probs = map(lambda x: x / total_prob, probs)
    return list(probs)


def calc_places_prob(
    horses,  # horse place probabilities
    cur_neg_prob=1,  # total amount of prob left for the rest of the horses in solution
    cur_adj_factor=1,  # probability adjustment using amount of prob left
    included_r=[],  # checks whether already included a runner in race solution
    recursion_level=0,
):
    """Recursively iterates through every horse placement position and calculates probability positions given the positions already allocated (if that makes any sense)"""
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
    for i in range(len(place_probs_r)):
        place_probs_r[i][0] = list(probs)[i]

    horses = dict(zip(horses.keys(), place_probs_r))
    return calc_places_prob(horses)


def check_profitable_ep_races(odds_df):
    # calc implied probability max loss / win extra place
    # edge = implied probability - horse place probability
    # if edge > 0
    for i, row in odds_df.iterrows():
        pass


def run_arb_place():
    pass


horses = calc_horse_place_probs(horses)
for horse, probs in horses.items():
    print(
        f"""{horse}: win - {1/probs[0]}
        2 places {places_lay[horse][0]} - {1/sum(probs[:2])}
        3 places  {places_lay[horse][1]} - {1/sum(probs[:3])}
        4 places {places_lay[horse][2]} - {1/sum(probs[:4])}
        """
    )
