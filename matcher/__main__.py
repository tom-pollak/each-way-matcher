import argparse
import sys

parser = argparse.ArgumentParser(description='Run EW matcher or output stats')
parser.add_argument('--run', help='Run the EW matcher', action='store_true')
parser.add_argument('--stats', help='Show stats', action='store_true')
parser.add_argument('--setup', help='Reset csv', action='store_true')
args = parser.parse_args()

if args.run:
    from .run import *
if args.stats:
    from .stats import output_profit, plot_bal_time_series_graph
    output_profit()
    plot_bal_time_series_graph()
if args.setup:
    from .output import reset_csv
    reset_csv()
if len(sys.argv) == 1:
    parser.print_help()
