import argparse
import sys

from .each_way import run_each_way
from .extra_places import run_extra_places
from .stats import output_profit, plot_bal_time_series_graph
from .setup import reset_csv

parser = argparse.ArgumentParser(
    description="Automated Each Way Matcher", prog="python3 -m matcher"
)
parser.add_argument("-r", "--run", help="Run the Each-way matcher", action="store_true")
parser.add_argument(
    "-p", "--punt", help="Punt bets on Sporting Index", action="store_true"
)
parser.add_argument("-l", "--lay", help="Lay on betfair", action="store_true")
parser.add_argument(
    "-e", "--extra", help="Run Extra Places matcher", action="store_true"
)
parser.add_argument("-s", "--stats", help="Display stats", action="store_true")
parser.add_argument("-g", "--graph", help="Generate graph", action="store_true")
parser.add_argument(
    "--setup", help="Reset csv and generate backup", action="store_true"
)
args = parser.parse_args()

if len(sys.argv) == 1:
    parser.print_help()

if args.setup:
    reset_csv()

if args.run and args.extra:
    print("Can't run both each-way matcher and extra place matcher")

elif args.run:
    if not args.punt and not args.lay:
        print("Must either punt, lay or both to run each-way matcher")
    else:
        run_each_way(args.punt, args.lay)

elif args.extra:
    run_extra_places()

if args.stats:
    output_profit()

if args.graph:
    plot_bal_time_series_graph()

sys.stdout.flush()
