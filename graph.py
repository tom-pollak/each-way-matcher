import pandas as pd
import matplotlib.pyplot as plt

headers = ['balance', 'current_time']
df = pd.read_csv('results.csv', names=headers)
print(df)

x = df['current_time']
y = df['balance']
plt.plot(x, y)
plt.gcf().autofmt_xdate()
plt.savefig('test.png')
