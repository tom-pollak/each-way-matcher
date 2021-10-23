from datetime import datetime
import matcher.sites.betfair as betfair

EXTRA_PLACE_POSITION = 4
RELEVANT_PLACES = 4

COMMISSION = 0.02


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
    ep_profit = win_profit = (
        bookie_stake * (bookie_odds - 1) + place_profit + bookie_stake
    )
    lose_profit = -bookie_stake * 2

    win_profit -= win_stake * (win_odds - 1) + place_stake * (place_odds - 1)
    ep_profit += win_stake * (win_odds - 1) + place_stake * (place_odds - 1)
    place_profit += win_stake - place_stake * (place_odds - 1) - commission_place
    lose_profit += win_stake + place_stake - commission_lose
    return (
        round(win_profit, 2),
        round(place_profit, 2),
        round(lose_profit, 2),
        round(ep_profit, 2),
    )


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


def get_ev_ep_races(
    bookie_odds,
    win_odds,
    place_odds,
    win_prob,
    place_prob,
    lose_prob,
    ep_prob,
    bookie_stake,
    win_stake,
    place_stake,
):
    # calc implied probability max loss / win extra place
    # edge = implied probability - horse place probability
    # if edge > 0
    win_profit, place_profit, lose_profit, ep_profit = calculate_profit(
        bookie_odds, bookie_stake, win_odds, win_stake, place_odds, place_stake, 5
    )
    print("\n------ PROFITS ------")
    print(
        f"Win profit: {win_profit}, Place profit: {place_profit}, Lose profit: {lose_profit}"
    )
    print(f"Extra place profit: {ep_profit}")
    ev = (
        win_profit * win_prob
        + place_profit * place_prob
        + lose_profit * lose_prob
        + ep_profit * ep_prob
    )
    print(f"Expected profit: £{round(ev, 2)}")


def run_arb_place():
    pass


def run_ep_cal():
    venue = input("Enter race venue: ")
    race_time = datetime.strptime(
        input("Enter datetime (D/M/YY h:mm): "), "%d/%m/%y %H:%M"
    )
    runners = betfair.get_race(venue, race_time)
    r_probs = calc_horse_place_probs({k: v["win"] for k, v in runners.items()})
    while True:
        print("------ HORSES -----")
        for i, (h, p) in enumerate(r_probs.items()):
            print(f"({i+1}) {h} - {round(p[3] * 100, 1)}%")

        horse_select = int(input("Select horse to calculate bet: "))
        h = list(runners)[horse_select - 1]
        print(f"{h}: {runners[h]}")
        bookie_odds = float(input("Bookie odds: "))

        win_prob = r_probs[h][0]
        place_prob = sum(r_probs[h][:3])
        lose_prob = sum(r_probs[h][4:])
        ep_prob = r_probs[h][3]
        bookie_stake, win_stake, place_stake = input(
            "Enter bookie stake, win_stake and place_stake seperated by a space: "
        ).split()
        get_ev_ep_races(
            bookie_odds,
            runners[h]["win"],
            runners[h]["place"],
            win_prob,
            place_prob,
            lose_prob,
            ep_prob,
            float(bookie_stake),
            float(win_stake),
            float(place_stake),
        )
