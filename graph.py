import matplotlib.pyplot as plt
import pandas as pd
import datetime
import time

RETURNS_CSV = 'returns/returns.csv'


def plot_bal_time_series_graph():
    # fig, ax = plt.subplots(figsize=(16, 9), dpi=100)

    balance = df['balance']
    plt.plot(balance)

    expected_return = df['expected_return']
    starting_balance = [df['balance'][0]]
    expected_return[0] += starting_balance
    expected_return.cumsum().plot()

    plt.gcf().autofmt_xdate()
    plt.savefig('graphs/balance.png')


custom_date_parser = lambda x: datetime.datetime(*(time.strptime(
    x, '%d/%m/%Y %H:%M:%S')[0:6]))

df = pd.read_csv(RETURNS_CSV,
                 header=0,
                 parse_dates=[7],
                 index_col=7,
                 date_parser=custom_date_parser,
                 squeeze=True)

plot_bal_time_series_graph(df)
