import argparse

parser = argparse.ArgumentParser(description='Run EW matcher or output stats')
parser.add_argument('--run', help='Run the EW matcher', action='store_true')
parser.add_argument('--stats', help='Show stats', action='store_true')
parser.add_argument('--graph', help='Create graph', action='store_true')
args = parser.parse_args()

if args.run:
    from .run import *
if args.stats:
    from .stats import output_profit
    output_profit()
if args.graph:
    from .stats import plot_bal_time_series_graph
    plot_bal_time_series_graph()
