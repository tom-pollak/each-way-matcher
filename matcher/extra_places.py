from .scrape_races import generate_df
from .betfair_scrape import get_odds


def run_extra_places():
    races_df, odds_df, min_runners_df = generate_df()
    print(races_df.iloc[0])
    get_odds(1.181022260)
