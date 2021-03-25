import requests

from .scrape_races import get_odds
from .get_races import generate_df

races_df, odds_df, min_runners_df = generate_df()


def run_extra_places():
    get_odds(str(races_df.iloc[0].win_market_id))
