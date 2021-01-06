import datetime
import sys
import time
import matplotlib.pyplot as plt
import pandas as pd

RETURNS_CSV = 'returns/returns.csv'
STARTING_BALANCE = 163.91


def custom_date_parser(x):
    if '/' not in x:
        return datetime.datetime(*(time.strptime(x, '%d %b %H:%M %Y')[0:6]))
    return datetime.datetime(*(time.strptime(x, '%d/%m/%Y %H:%M:%S')[0:6]))


def calc_unfinished_races(index=-1):
    in_bet_balance = 0
    mask = (df['date_of_race'] >
            df.index.values[index]) & (df.index <= df.index.values[index])
    races = df.loc[mask]
    for _, row in races.iterrows():
        stake = row['ew_stake'] * 2
        # print(row['win_stake'], row['lay_odds'], row['place_stake'],
        #       row['lay_odds_place'])
        if row['is_lay']:
            liability = row['win_stake'] * (row['lay_odds'] -
                                            1) + row['place_stake'] * (
                                                row['lay_odds_place'] - 1)
        else:
            liability = 0
        in_bet_balance += (stake + liability)
    return round(in_bet_balance, 2)


def output_profit():
    # starting_balance = df['balance'].values[0] + df['betfair_balance'].values[
    #     0] + calc_unfinished_races(0)
    # 03 Jan 00:01 2021,Starting Balance,2.25,N/A,0.58,59.11,99.91,03/01/2021 00:00:00,0%,0,2.42,1.15,0,0,93.28,0.12,False,0,0,0
    def get_today_starting_balance():
        try:
            today_first_bet = df.loc[datetime.datetime.now().strftime(
                '%Y-%m-%d')].index.values[0]
        except KeyError:
            return None
        count = 0
        for index, _ in df.iterrows():
            if today_first_bet == index:
                break
            count += 1

        return df.loc[datetime.datetime.now().strftime(
            '%Y-%m-%d')]['balance'].values[0] + df.loc[
                datetime.datetime.now().strftime('%Y-%m-%d')][
                    'betfair_balance'].values[0] + calc_unfinished_races(count)

    today_starting_balance = get_today_starting_balance()

    current_sporting_index_balance = df['balance'].values[-1]
    current_betfair_balance = df['betfair_balance'].values[-1]
    in_bet_balance = calc_unfinished_races()
    current_balance = current_sporting_index_balance + current_betfair_balance + in_bet_balance

    total_profit = round(current_balance - STARTING_BALANCE, 2)
    if not today_starting_balance:
        profit_today = 0
    else:
        profit_today = round(current_balance - today_starting_balance, 2)
    if total_profit == 0: total_percentage_profit = 0
    else:
        total_percentage_profit = round(
            (total_profit / STARTING_BALANCE) * 100, 2)

    if profit_today == 0: today_percentage_profit = 0
    else:
        today_percentage_profit = round(
            (profit_today / today_starting_balance) * 100, 2)
    print(
        f'Total profit: £{format(total_profit, ".2f")} ({total_percentage_profit}%)'
    )
    print(
        f'Profit today: £{format(profit_today, ".2f")} ({today_percentage_profit}%)'
    )
    print(
        f'Sporting index balance: £{current_sporting_index_balance} Betfair balance: £{current_betfair_balance} Balance in bets: £{in_bet_balance}'
    )


def plot_bal_time_series_graph():
    # fig, ax = plt.subplots(figsize=(16, 9), dpi=100)

    balance = df['balance'] + df['betfair_balance']
    plt.plot(balance)

    for i in range(len(balance)):
        # print(balance[i], calc_unfinished_races(i))
        balance[i] += calc_unfinished_races(i)

    plt.plot(balance)

    expected_return = df['expected_return'] + df['arbritrage_profit']
    # starting_balance = df['balance'].values[0] + df['betfair_balance'].values[0]
    expected_return[0] += STARTING_BALANCE
    expected_return.cumsum().plot()

    plt.gcf().autofmt_xdate()
    plt.savefig('graphs/balance.png')


# custom_date_parser = lambda x: datetime.datetime(*(time.strptime(
#     x, '%d/%m/%Y %H:%M:%S')[0:6]))

df = pd.read_csv(RETURNS_CSV,
                 header=0,
                 parse_dates=[7, 0],
                 index_col=7,
                 date_parser=custom_date_parser,
                 squeeze=True)

output_profit()
plot_bal_time_series_graph()
sys.stdout.flush()
