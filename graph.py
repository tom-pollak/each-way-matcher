import pandas as pd
import matplotlib.pyplot as plt


def plot_bal_time_series_graph(df):
    y = df['balance']
    # print(y)
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

    plt.plot(y)
    plt.gcf().autofmt_xdate()
    plt.savefig('graphs/expected-returns.png')


df = pd.read_csv('returns.csv',
                 header=0,
                 parse_dates=[7],
                 index_col=7,
                 squeeze=True)
# print(df)
plot_bal_time_series_graph(df)
plot_expected_profit(df)
