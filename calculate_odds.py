import math


def kelly_criterion(horse_odds, lay_odds, lay_odds_place, place, balance):
    n = 0.5 * (horse_odds - 1) / place
    m = horse_odds * 0.5 - 0.5 + n
    n -= 0.5  # - the stake lost from losing win place
    # print(m, n)

    p = 1 / lay_odds
    q = 1 / (lay_odds_place) - p
    # print(p, q)

    A = m * n
    B = (p + q) * m * n + p * n + q * m - m - n
    C = p * m + q * n - (1 - p - q)  # Expected profit on 0.5 unit EW bet
    # print(A, B, C)

    try:
        stake_proportion = (B + math.sqrt(B**2 + 4 * A * C)) / (4 * A)
    except ZeroDivisionError:
        print('ERROR Divided by 0')
        print(m, n)
        print(p, q)
        print(A, B, C)
        return 0, 0, '0%'
    # print(stake_proportion)
    ew_stake = stake_proportion * balance
    # print(ew_stake)
    return round(ew_stake, 2), round(C * ew_stake * 2,
                                     2), str(round(C * 100, 2)) + '%'


# kelly_criterion(12, 12, 3.2, 5, 10000)
