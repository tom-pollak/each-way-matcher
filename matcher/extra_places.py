from .scrape_races import generate_df
from .betfair_scrape import get_odds

races_df, odds_df, min_runners_df = generate_df()


def run_extra_places():
    print(races_df.iloc[0])
    get_odds(str(races_df.iloc[0].win_market_id))
