import sys
import traceback
from time import sleep, time
from datetime import datetime

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import WebDriverException

from .setup import setup_selenium, login, check_vars
from .calculate import (
    calculate_stakes,
    calculate_profit,
    kelly_criterion,
    check_repeat_bets,
    maximize_arb,
    check_stakes,
    check_odds_changes,
)
from .output import (
    update_csv_sporting_index,
    update_csv_betfair,
    show_info,
    output_lay_ew,
    output_race,
)
from .exceptions import MatcherError
from matcher.sites.odds_monkey import (
    find_races,
    refresh_odds_monkey,
    open_betfair_oddsmonkey,
    get_no_rows,
)
from matcher.sites.betfair_api import (
    lay_ew,
    get_betfair_balance,
    login_betfair,
    get_race,
    get_race_odds,
    cancel_unmatched_bets,
)
from matcher.sites.sporting_index import (
    setup_sporting_index,
    sporting_index_bet,
    refresh_sporting_index,
    get_balance_sporting_index,
)

REFRESH_TIME = 60


def place_arb(
    selection_id,
    market_ids,
    bookie_stake,
    bookie_odds,
    win_stake,
    win_odds,
    place_stake,
    place_odds,
    place_payout,
):
    first_run = True
    while first_run or not lay_win["matched"] or not lay_place["matched"]:
        lay_win, lay_place = lay_ew(
            market_ids,
            selection_id,
            win_stake,
            win_odds,
            place_stake,
            place_odds,
        )
        cancel_unmatched_bets()
        if first_run:
            first_run = False
            win_stake = lay_win["matched_stake"]
            place_stake = lay_place["matched_stake"]
            init_win_odds = lay_win["odds"]
            init_place_odds = lay_place["odds"]
        else:
            win_stake += lay_win["matched_stake"] * lay_win["odds"] / init_win_odds
            place_stake += (
                lay_place["matched_stake"] * lay_place["odds"] / init_place_odds
            )

        win_profit, place_profit, lose_profit = calculate_profit(
            bookie_odds,
            bookie_stake,
            init_win_odds,
            win_stake,
            init_place_odds,
            place_stake,
            place_payout,
        )

        win_odds = get_race_odds(market_ids["Win"])["lay_odds_1"]
        place_odds = get_race_odds(market_ids["Place"])["lay_odds_1"]
        new_win_stake, new_place_stake = maximize_arb(
            win_odds, place_odds, win_profit, place_profit, lose_profit
        )
        betfair_balance = get_betfair_balance()
        if not check_stakes(
            None,
            betfair_balance,
            bookie_stake,
            new_win_stake,
            win_odds,
            new_place_stake,
            place_odds,
        ):
            break

    return win_stake, init_win_odds, place_stake, init_place_odds


def betfair_bet(driver, race):
    def check_start_time():
        minutes_until_race = (
            datetime.strptime(race["date_of_race"], "%d %b %H:%M %Y") - datetime.now()
        ).total_seconds() / 60
        if minutes_until_race <= 2:
            print("Race too close to start time: %s" % minutes_until_race)
            return False
        return True

    if not check_start_time():
        return
    start = time()
    race["betfair_balance"] = get_betfair_balance()
    (
        stakes_ok,
        race["bookie_stake"],
        race["win_stake"],
        race["place_stake"],
    ) = calculate_stakes(
        race["balance"],
        race["betfair_balance"],
        race["bookie_stake"],
        race["win_stake"],
        race["win_odds"],
        race["place_stake"],
        race["place_odds"],
    )

    if not stakes_ok:
        print(f"Stakes not ok: {race['win_stake']}, {race['place_stake']}")
        return

    profits = calculate_profit(
        race["bookie_odds"],
        race["bookie_stake"],
        race["win_odds"],
        race["win_stake"],
        race["place_odds"],
        race["place_stake"],
        race["place_payout"],
    )
    if min(*profits) < 0:
        stake_proportion = maximize_arb(race["win_odds"], race["place_odds"], *profits)
        if stake_proportion == 0:
            print(f"Arb bet not profitable: {profits}")
            return

        race["bookie_stake"] = race["bookie_stake"] * stake_proportion
        race["win_stake"] = race["win_stake"] * stake_proportion
        race["place_stake"] = race["place_stake"] * stake_proportion
        stakes_ok = check_stakes(
            race["balance"],
            race["betfair_balance"],
            race["bookie_stake"],
            race["win_stake"],
            race["win_odds"],
            race["place_stake"],
            race["place_odds"],
        )
        if not stakes_ok:
            print(f"Profits below 0: {profits}")
            print(race["bookie_stake"], race["win_stake"], race["place_stake"])
            print(race["bookie_odds"], race["win_odds"], race["place_odds"])
            print(f"stake_proportion: {stake_proportion} too small")
            return

    market_ids, selection_id, got_race, race["horse_name"] = get_race(
        race["date_of_race"], race["venue"], race["horse_name"]
    )
    if not got_race:
        print("Couldn't get race")
        return

    win_horse_odds = get_race_odds(market_ids["Win"])
    place_horse_odds = get_race_odds(market_ids["Place"])
    check_odds_changes(race, win_horse_odds, place_horse_odds)

    race, bet_made = sporting_index_bet(driver, race, market_ids, betfair=True)
    if bet_made is None:
        print(
            f"Horse not found: {race['horse_name']}  venue: {race['venue']}  race time: {race['date_of_race']}"
        )
    elif bet_made:
        (
            race["win_stake"],
            race["win_odds"],
            race["place_stake"],
            race["place_odds"],
        ) = place_arb(
            selection_id,
            market_ids,
            race["bookie_stake"],
            race["bookie_odds"],
            race["win_stake"],
            race["win_odds"],
            race["place_stake"],
            race["place_odds"],
            race["place_payout"],
        )
        (
            race["win_profit"],
            race["place_profit"],
            race["lose_profit"],
        ) = calculate_profit(
            race["bookie_odds"],
            race["bookie_stake"],
            race["win_odds"],
            race["win_stake"],
            race["place_odds"],
            race["place_stake"],
            race["place_payout"],
        )
        race["betfair_balance"] = get_betfair_balance()
        race["balance"] = get_balance_sporting_index(driver)
        min_profit = min(race["win_profit"], race["place_profit"], race["lose_profit"])

        output_lay_ew(
            race,
            min_profit,
        )
        update_csv_betfair(
            race,
            min_profit,
        )
        end = time()


def evaluate_sporting_index_bet(driver, race):
    (
        race["bookie_stake"],
        race["expected_return"],
        race["expected_value"],
    ) = kelly_criterion(
        race["bookie_odds"],
        race["win_odds"],
        race["place_odds"],
        race["place_payout"],
        race["balance"],
    )

    if race["bookie_stake"] < 0.1:
        return False

    _, _, _, race["horse_name"] = get_race(
        race["date_of_race"], race["venue"], race["horse_name"]
    )

    race, bet_made = sporting_index_bet(driver, race)
    if bet_made is None:  # horse not found
        print(
            f"Horse not found: {race['horse_name']}  venue: {race['venue']}  race time: {race['date_of_race']}"
        )
        return False
    if bet_made:
        output_race(driver, race)
        update_csv_sporting_index(driver, race)
        return True
    return False


def start_sporting_index(driver):
    race = {"balance": get_balance_sporting_index(driver)}
    processed_horses = []
    driver.switch_to.window(driver.window_handles[0])
    refresh_odds_monkey(driver)
    if not driver.find_elements_by_class_name("rgNoRecords"):
        for row in range(get_no_rows(driver)):
            horse_name = (
                WebDriverWait(driver, 60)
                .until(
                    EC.visibility_of_element_located(
                        (
                            By.XPATH,
                            f'//table//tr[@id="dnn_ctr1157_View_RadGrid1_ctl00__{row}"]//td[9]',
                        )
                    )
                )
                .text.title()
            )
            if horse_name not in processed_horses:
                race.update(find_races(driver, row, 0))
                processed_horses.append(race["horse_name"])
                if check_repeat_bets(
                    race["horse_name"], race["date_of_race"], race["venue"]
                ):
                    evaluate_sporting_index_bet(driver, race)

            driver.switch_to.window(driver.window_handles[0])
            driver.switch_to.default_content()
            sys.stdout.flush()


def start_betfair(driver):
    race = {"balance": get_balance_sporting_index(driver)}
    processed_horses = []
    driver.switch_to.window(driver.window_handles[2])
    refresh_odds_monkey(driver, betfair=True)
    if not driver.find_elements_by_class_name("rgNoRecords"):
        for row in range(get_no_rows(driver)):
            horse_name = (
                WebDriverWait(driver, 60)
                .until(
                    EC.visibility_of_element_located(
                        (
                            By.XPATH,
                            f'//table//tr[@id="dnn_ctr1157_View_RadGrid1_ctl00__{row}"]//td[9]',
                        )
                    )
                )
                .text.title()
            )
            if horse_name not in processed_horses:
                race.update(find_races(driver, row, 2))
                processed_horses.append(race["horse_name"])
                betfair_bet(driver, race)
            driver.switch_to.window(driver.window_handles[2])
            driver.switch_to.default_content()
            sys.stdout.flush()


def start_matcher(driver, lay):
    START_TIME = time()
    setup_sporting_index(driver)
    open_betfair_oddsmonkey(driver)
    count = 0
    driver.switch_to.window(driver.window_handles[0])
    while True:
        loop_time = time()
        # So sporting index dosent logout
        if count % 4 == 0:
            refresh_sporting_index(driver)
        if count % 10 == 0:
            show_info(count, START_TIME)

        if lay:
            start_betfair(driver)
        start_sporting_index(driver)
        sys.stdout.flush()
        diff = time() - loop_time
        if diff < REFRESH_TIME:
            sleep(REFRESH_TIME - diff)
        count += 1


def run_each_way(lay):
    if datetime.now().hour < 7:
        print("\nMatcher started too early (before 7am)")
        return
    print(f'Started at: {datetime.now().strftime("%H:%M:%S %d/%m/%Y")}')

    check_vars()
    while True:
        driver = setup_selenium()
        sys.stdout.flush()
        try:
            login(driver)
            start_matcher(driver, lay)
        except MatcherError as e:
            print(e)
            # print(traceback.format_exc())
        except KeyboardInterrupt:
            break
        except WebDriverException as e:
            print("WebDriver error occured: %s" % e)
            print(traceback.format_exc())
        except Exception as e:
            print("Unknown error occured: %s" % e)
            print(traceback.format_exc())
        finally:
            sys.stdout.flush()
            driver.quit()