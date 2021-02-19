import argparse
import sys

from .run import run_matcher
from .stats import output_profit, plot_bal_time_series_graph
from .output import reset_csv

parser = argparse.ArgumentParser(description='Run EW matcher or output stats',
                                 prog='python3 -m matcher')
parser.add_argument('-r',
                    '--run',
                    help='Run the EW matcher',
                    action='store_true')
parser.add_argument('-s', '--stats', help='Display stats', action='store_true')
parser.add_argument('-g',
                    '--graph',
                    help='Generate graph',
                    action='store_true')
parser.add_argument('--setup', help='Reset csv', action='store_true')
args = parser.parse_args()

if args.run:
    run_matcher()

if args.stats:
    output_profit()

if args.graph:
    plot_bal_time_series_graph()

if args.setup:
    reset_csv()

if len(sys.argv) == 1:
    parser.print_help()
