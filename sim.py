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
        count = 0
        for i in range(1000):
            if simulate_bet(stake, odds, rating, balance):
                count += 1
        stake -= (950 - count) / 1000 * stake
        # print(stake, count / 10)

    if stake < 0.1:
        count = 0
        for i in range(1000):
            if simulate_bet(0.1, odds, rating, balance):
                count += 1
        if count >= 800:
            # print(0.1, count / 10)
            return 0.1, (count / 10)
        else:
            # print(False, count / 10)
            return False, (count / 10)

    # print(stake, count / 10)
    return round(stake, 2), (count / 10)
