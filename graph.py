import matplotlib.pyplot as plt
import pandas as pd


def plot_bal_time_series_graph(df):
    y = df['balance']
    # print(y)
    # x = matplotlib.dates.date2num()
    # formatter = matplotlib.dates.DateFormatter('%H:%M:%S')

    fig, ax = plt.subplots(figsize=(16, 9), dpi=100)
    plt.plot(y)

    plt.gcf().autofmt_xdate()
    plt.savefig('graphs/balance.png')


def plot_expected_profit(df):
    print(df)
    balance = df['balance'].iloc[0]
    print(balance)
    bal_list = []

    for i in range(len(df)):
        balance += df['rating'].iloc[i] / 100 * df['ew_stake'].iloc[i]
        bal_list.append([balance, df['current_time'].iloc[i]])
    print(bal_list)
    df = pd.DataFrame(bal_list, columns=['balance', 'current_time'])

    plt.plot(bal_list)
    plt.gcf().autofmt_xdate()
    plt.savefig('graphs/expected-returns.png')


import datetime
import time

custom_date_parser = lambda x: datetime.datetime(*(time.strptime(
    x, '%d/%m/%Y %H:%M:%S')[0:6]))
df = pd.read_csv('returns.csv',
                 header=0,
                 parse_dates=[7],
                 index_col=7,
                 date_parser=custom_date_parser,
                 squeeze=True)
print(df)
# print(df)
plot_bal_time_series_graph(df)
# plot_expected_profit(df)
