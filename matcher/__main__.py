import argparse
import sys

from .run import run_matcher
from .extra_places import run_extra_place
from .stats import output_profit, plot_bal_time_series_graph
from .output import reset_csv

parser = argparse.ArgumentParser(
    description="Automated Each Way Matcher", prog="python3 -m matcher"
)
parser.add_argument("-r", "--run", help="Run the Each-way matcher", action="store_true")
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
    print("Can't run both Each-way matcher and Extra place matcher")

elif args.run:
    run_matcher()

elif args.extra:
    run_extra_place()

if args.stats:
    output_profit()

if args.graph:
    plot_bal_time_series_graph()
