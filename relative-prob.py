RELEVANT_PLACES = 2
probs = [0.25, 0.1, 0.15, 0.13, 0.12, 0.05, 0.17, 0.03]

place_probs_r = [[0 for _ in range(len(probs))] for _ in range(len(probs))]
place_probs_r[0] = probs


def normalize_probs(probs):
    total_prob = sum(probs)
    if total_prob <= 0:
        print("Invalid probabilities: Total probability = %s" % total_prob)
        return None
    if total_prob != 1:
        print("Normalizing prob by a factor of %s" % total_prob)
        probs = map(lambda x: x / total_prob, probs)
    return probs


def calc_places_prob(
    place_probs_r,  # runner place probabilities
    n=None,  # number of runners
    cur_neg_prob=1,  # tot amount of prob left for the rest of the horses in solution
    cur_adj_factor=1,  # probability adjustment using amount of prob left
    included_r={},  # checks whether already included a runner in race solution
    recursion_level=0,  # recursion level
):
    """Recursively iterates through every horse placement position and calculates probability positions given the positions already allocated (if that makes any sense)"""
    recursion_level += 1
    if n is None:
        n = len(place_probs_r[0])

    for i in range(n):
        print(i, cur_adj_factor)
        if included_r.get(i) is not None:
            continue
        prob = place_probs_r[0][i]
        if recursion_level > 1:
            place_probs_r[recursion_level - 1][i] += prob * cur_adj_factor
        if recursion_level < RELEVANT_PLACES:
            neg_prob = cur_neg_prob - prob
            adj_factor = cur_adj_factor * prob / neg_prob
            print("\t%s %s" % (i, adj_factor))
            included_r[i] = True
            calc_places_prob(
                place_probs_r, n, neg_prob, adj_factor, included_r, recursion_level
            )
            del included_r[i]


def check_profitable_ep_races(odds_df):
    # calc implied probability max loss / win extra place
    # edge = implied probability - horse place probability
    # if edge > 0
    for i, row in odds_df.iterrows():
        pass


probs = normalize_probs(probs)
calc_places_prob(place_probs_r=place_probs_r)

for i, place in enumerate(place_probs_r):
    print("%s: %s" % (i + 1, place))
