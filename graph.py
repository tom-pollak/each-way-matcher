import pandas as pd
import matplotlib.pyplot as plt


def plot_bal_time_series_graph(df):
    y = df['balance']
    plt.plot(y)
    plt.gcf().autofmt_xdate()
    plt.savefig('graphs/balance.png')


df = pd.read_csv('returns.csv',
                 header=0,
                 parse_dates=[7],
                 index_col=7,
                 squeeze=True)
plot_bal_time_series_graph(df)
