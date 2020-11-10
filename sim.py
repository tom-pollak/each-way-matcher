from random import uniform


def simulate_bet(stake, odds, rating, balance):
    stake *= 2
    for i in range(1000):
        if uniform(0, round(odds / (rating / 100), 2)) <= 1:
            balance += odds * stake
        else:
            balance -= stake
        if balance <= 0:
            return False
    return True


def find_stake(odds, rating, balance):
    count = 0
    stake = 0.1 * balance
    while not 950 <= count <= 975:
        print(stake, count / 10)
        count = 0
        for j in range(1000):
            if simulate_bet(stake, odds, rating, balance):
                count += 1
        stake -= round((950 - count) / 1000 * stake, 2)

    if stake < 0.1:
        count = 0
        for i in range(1000):
            if simulate_bet(stake, odds, rating, balance):
                count += 1
        if count >= 750:
            return 0.1, (count / 10)
        else:
            return False, (count / 10)

    return round(stake, 2), (count / 10)
