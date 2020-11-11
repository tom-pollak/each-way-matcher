from random import uniform


def simulate_bet(stake, odds, rating, balance):
    original_bal = balance
    stake *= 2
    for i in range(1000):
        if uniform(0, round(odds / (rating / 100), 2)) <= 1:
            balance += odds * stake
        balance -= stake
        if balance <= 0:
            return False
    if balance > original_bal:
        # print(balance)
        return True
    else:
        # print(balance)
        return False


import numpy as np


def find_stake(odds, rating, balance):
    count = 0
    stake = 0.1 * balance
    percentage_list = []
    per_list_count = 0
    old_std = False
    while not 950 <= count <= 975 or per_list_count >= 40:
        count = 0
        for j in range(1000):
            if simulate_bet(stake, odds, rating, balance):
                count += 1
        percentage_list.append(count)
        stake -= (950 - count) / 1000 * stake
        # print(stake, count / 10)
        per_list_count += 1

        if per_list_count % 5 == 0:
            grads = np.gradient(percentage_list)
            # print(np.mean(grads))
            if np.mean(grads) <= 5:
                # print(stake, count / 10)
                if count >= 800:
                    return round(stake, 2), (count / 10)
                return False, (count / 10)
            percentage_list = []

    if stake < 0.1 or per_list_count >= 40:
        return False, (count / 10)

    # print(stake, count / 10)
    return round(stake, 2), (count / 10)
