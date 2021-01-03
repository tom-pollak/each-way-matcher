import datetime
import time
import matplotlib.pyplot as plt
import pandas as pd

RETURNS_CSV = 'returns/returns.csv'


def custom_date_parser(x):
    return datetime.datetime(*(time.strptime(x, '%d/%m/%Y %H:%M:%S')[0:6]))


def output_profit():
    starting_balance = df['balance'].values[0] + df['betfair_balance'].values[0]
    today_starting_balance = df.loc[datetime.datetime.now().strftime(
        '%Y-%m-%d')]['balance'].values[0] + df.loc[datetime.datetime.now(
        ).strftime('%Y-%m-%d')]['betfair_balance'].values[0]

    current_sporting_index_balance = df['balance'].values[-1]
    current_betfair_balance = df['betfair_balance'].values[-1]
    current_balance = current_sporting_index_balance + current_betfair_balance
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
        f'Sporting index balance: £{current_sporting_index_balance} Betfair balance: £{current_betfair_balance}'
    )


def plot_bal_time_series_graph():
    # fig, ax = plt.subplots(figsize=(16, 9), dpi=100)

    balance = df['balance'] + df['betfair_balance']
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
                 parse_dates=[7],
                 index_col=7,
                 date_parser=custom_date_parser,
                 squeeze=True)

output_profit()
plot_bal_time_series_graph()
