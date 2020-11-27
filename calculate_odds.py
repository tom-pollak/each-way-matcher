import math


def kelly_criterion(horse_odds, rating, place, balance):
    n = 0.5 * (horse_odds - 1) / place - 0.5
    m = horse_odds * 0.5 + n
    print(m, n)

    p = 1 / horse_odds
    q = 1 / (((horse_odds / (rating / 100)) - 1) / place)
    print(p, q)

    A = m * n
    B = (p + q) * m * n + p * n + q * m - m - n
    C = p * m + q * n - (1 - p - q) # Expected profit on 0.5 unit EW bet
    print(A, B, C)

    stake_proportion = (B + math.sqrt(B**2 + 4 * A * C)) / (4 * A)
    print(stake_proportion)
    ew_stake = stake_proportion * balance
    print(ew_stake)
    return ew_stake


kelly_criterion(11, 100, 5, 50)
