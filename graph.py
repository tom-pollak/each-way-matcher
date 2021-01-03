import datetime
import time
import matplotlib.pyplot as plt
import pandas as pd

RETURNS_CSV = 'returns/returns.csv'


def custom_date_parser(x):
    if '/' not in x:
        return datetime.datetime(*(time.strptime(x, '%d %b %H:%M %Y')[0:6]))
    return datetime.datetime(*(time.strptime(x, '%d/%m/%Y %H:%M:%S')[0:6]))


def calc_unfinished_races(index=-1):
    in_bet_balance = 0
    mask = (df['date_of_race'] >
            df.index.values[index]) & (df.index <= df.index.values[index])
    races = df.loc[mask]
    for index, row in races.iterrows():
        if not row['is_lay']:
            stake = row['ew_stake'] * 2
            liability = 0
        else:
            stake = row['ew_stake'] + row['win_stake'] + row['place_stake']
            liability = row['win_stake'] * (row['lay_odds'] -
                                            1) + row['place_stake'] * (
                                                row['lay_odds_place'] - 1)
        in_bet_balance += (stake + liability)
    return round(in_bet_balance, 2)


def output_profit():
    starting_balance = df['balance'].values[0] + df['betfair_balance'].values[0]
    today_starting_balance = df.loc[datetime.datetime.now().strftime(
        '%Y-%m-%d')]['balance'].values[0] + df.loc[datetime.datetime.now(
        ).strftime('%Y-%m-%d')]['betfair_balance'].values[0]

    current_sporting_index_balance = df['balance'].values[-1]
    current_betfair_balance = df['betfair_balance'].values[-1]
    in_bet_balance = calc_unfinished_races()
    current_balance = current_sporting_index_balance + current_betfair_balance + in_bet_balance

    total_profit = round(current_balance - starting_balance, 2)
    profit_today = round(current_balance - today_starting_balance, 2)
    if total_profit == 0: total_percentage_profit = 0
    else:
        total_percentage_profit = round(starting_balance / total_profit, 2)

    if profit_today == 0: today_percentage_profit = 0
    else:
        today_percentage_profit = round(today_starting_balance / profit_today,
                                        2)
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

    for i, b in enumerate(balance):
        balance[i] = b + calc_unfinished_races(i)

    plt.plot(balance)

    expected_return = df['expected_return'] + df['arbritrage_profit']
    starting_balance = df['balance'].values[0] + df['betfair_balance'].values[0]
    expected_return[0] += starting_balance
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
