import os
import sys
import traceback
from time import sleep, time
from datetime import datetime

from dotenv import load_dotenv
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import WebDriverException

from .setup import setup_selenium, check_vars
from .calculate import (
    calculate_stakes,
    calculate_profit,
    calculate_stakes_from_profit,
    calculate_expected_return,
    kelly_criterion,
    minimize_loss,
    check_stakes,
    maximize_arb,
    check_start_time,
    get_valid_horse_name,
    get_max_stake,
    bet_profitable,
)
from .stats import check_repeat_bets, calc_unfinished_races
from .output import update_csv, show_info, ouput_lay, output_punt, alert_low_funds
from .exceptions import MatcherError
import matcher.sites.odds_monkey as odds_monkey
import matcher.sites.sporting_index as sporting_index
import matcher.sites.betfair as betfair

BASEDIR = os.path.abspath(os.path.dirname(__file__) + "/../")
load_dotenv(os.path.join(BASEDIR, ".env"))
REFRESH_TIME = float(os.environ.get("REFRESH_TIME"))


def place_arb(
    selection_id,
    market_ids,
    horse_name,
    bookie_stake,
    bookie_odds,
    win_stake,
    win_odds,
    place_stake,
    place_odds,
    place_payout,
    profits=(0, 0, 0),
):
    lay_win, lay_place = betfair.make_bets(
        market_ids,
        selection_id,
        win_stake,
        win_odds,
        place_stake,
        place_odds,
    )
    bet_info = {
        "win": {"odds": 0, "stake": 0},
        "place": {"odds": 0, "stake": 0},
    }
    betfair.cancel_unmatched_bets()
    bet_info.update(
        betfair.get_bets_by_bet_id(
            market_ids["win"],
            market_ids["place"],
            lay_win["bet_id"],
            lay_place["bet_id"],
        )
    )
    new_profits = calculate_profit(
        bookie_odds,
        bookie_stake,
        bet_info["win"]["odds"],
        bet_info["win"]["stake"],
        bet_info["place"]["odds"],
        bet_info["place"]["stake"],
        place_payout,
    )
    profits = tuple(map(sum, zip(profits, new_profits)))

    if not lay_win["matched"] or not lay_place["matched"]:
        print("bet not matched")
        print(lay_win)
        print(lay_place)
        win_odds, win_available = betfair.get_odds(market_ids["win"], selection_id)
        place_odds, place_available = betfair.get_odds(
            market_ids["place"], selection_id
        )
        betfair_balance = betfair.get_balance()
        win_stake, place_stake = minimize_loss(
            win_odds,
            place_odds,
            win_available,
            place_available,
            profits,
            betfair_balance,
            place_payout,
        )
        if not check_stakes(
            0,
            betfair_balance,
            0,
            win_stake,
            win_odds,
            win_available,
            place_stake,
            place_odds,
            place_available,
        ):
            return profits
        profits = place_arb(
            selection_id,
            market_ids,
            horse_name,
            0,
            0,
            win_stake,
            win_odds,
            place_stake,
            place_odds,
            place_payout,
            profits,
        )
    return profits


def evaluate_arb(driver, race):
    if not check_start_time(race, secs=45):
        return
    race["bet_type"] = "Arb"
    race["betfair_balance"] = betfair.get_balance()
    horses = betfair.get_horses(race["venue"], race["race_time"]).keys()
    race["horse_name"], betfair_horse_name = get_valid_horse_name(
        horses, race["horse_name"]
    )
    market_ids, selection_id = betfair.get_race_ids(
        race["race_time"], race["venue"], betfair_horse_name
    )

    race["win_odds"], win_available = betfair.get_odds(market_ids["win"], selection_id)
    race["place_odds"], place_available = betfair.get_odds(
        market_ids["place"], selection_id
    )
    if min(win_available, place_available) == 0:
        return

    max_bookie_stake, max_win_stake, max_place_stake = get_max_stake(
        race["bookie_odds"],
        race["win_odds"],
        race["place_odds"],
        win_available,
        place_available,
        race["place_payout"],
    )
    (
        stakes_ok,
        race["bookie_stake"],
        race["win_stake"],
        race["place_stake"],
    ) = calculate_stakes(
        race["bookie_balance"],
        race["betfair_balance"],
        max_bookie_stake,
        max_win_stake,
        race["win_odds"],
        win_available,
        max_place_stake,
        race["place_odds"],
        place_available,
    )

    if not stakes_ok:
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
        stake_proportion = maximize_arb(
            race["bookie_balance"],
            race["betfair_balance"],
            race["win_odds"],
            race["place_odds"],
            *profits,
        )
        bet_types, _, new_profits = check_repeat_bets(
            race["horse_name"], race["race_time"], race["venue"]
        )
        if "Lay Punt" in bet_types:
            new_stake_proportion = maximize_arb(
                race["bookie_balance"],
                race["betfair_balance"],
                race["win_odds"],
                race["place_odds"],
                *tuple(map(sum, zip(profits, new_profits))),
            )
            if stake_proportion != 1 or new_stake_proportion != 1:
                return

        race["bookie_stake"] = round(race["bookie_stake"] * stake_proportion, 2)
        race["win_stake"] = round(race["win_stake"] * stake_proportion, 2)
        race["place_stake"] = round(race["place_stake"] * stake_proportion, 2)

        if not bet_profitable(race):
            return

        stakes_ok = check_stakes(
            race["bookie_balance"],
            race["betfair_balance"],
            race["bookie_stake"],
            race["win_stake"],
            race["win_odds"],
            win_available,
            race["place_stake"],
            race["place_odds"],
            place_available,
        )
        if not stakes_ok:
            return

    if not betfair.check_odds(race, market_ids, selection_id):
        evaluate_arb(driver, race)
        return
    bet_made = sporting_index.make_bet(driver, race, market_ids, selection_id, lay=True)
    if not bet_made:
        return

    race["win_profit"], race["place_profit"], race["lose_profit"] = place_arb(
        selection_id,
        market_ids,
        race["horse_name"],
        race["bookie_stake"],
        race["bookie_odds"],
        race["win_stake"],
        race["win_odds"],
        race["place_stake"],
        race["place_odds"],
        race["place_payout"],
    )
    if min(race["win_profit"], race["place_profit"], race["lose_profit"]) > 0:
        race["bet_type"] = "Arb"
    else:
        race["bet_type"] = "Lay Punt"

    race["win_odds"], win_available = betfair.get_odds(market_ids["win"], selection_id)
    race["place_odds"], place_available = betfair.get_odds(
        market_ids["place"], selection_id
    )
    race["win_stake"], race["place_stake"] = calculate_stakes_from_profit(
        race["place_profit"],
        race["lose_profit"],
        race["bookie_stake"],
        race["bookie_odds"],
        race["place_odds"],
        race["place_payout"],
    )
    race["betfair_balance"] = betfair.get_balance()
    race["bookie_balance"] = sporting_index.get_balance(driver)
    race["betfair_exposure"] = betfair.get_exposure()
    (
        race["exp_value"],
        race["exp_growth"],
        race["exp_return"],
    ) = calculate_expected_return(
        race["bookie_balance"] + race["betfair_balance"] + calc_unfinished_races(),
        race["win_odds"],
        race["place_odds"],
        race["win_profit"],
        race["place_profit"],
        race["lose_profit"],
    )

    ouput_lay(race)
    update_csv(race)
    alert_low_funds(race)


def evaluate_punt(driver, race):
    race["bet_type"] = "Punt"
    race["win_stake"] = race["place_stake"] = 0
    horses = betfair.get_horses(race["venue"], race["race_time"]).keys()
    race["horse_name"], _ = get_valid_horse_name(horses, race["horse_name"])
    bet_types, win_odds_proportion, _ = check_repeat_bets(
        race["horse_name"], race["race_time"], race["venue"]
    )
    if "Punt" in bet_types:
        return

    race["bookie_stake"] = kelly_criterion(
        race["bookie_odds"],
        race["win_odds"] / win_odds_proportion,
        race["place_odds"],
        race["place_payout"],
        race["bookie_balance"],
    )

    if not bet_profitable(race):
        return

    if race["bookie_stake"] < 0.1:
        return

    bet_made = sporting_index.make_bet(driver, race)
    if bet_made is None:  # horse not found
        print(
            f"Horse not found: {race['horse_name']}  venue: {race['venue']}  race time: {race['race_time']}"
        )
        return

    if not bet_made:
        return

    race["win_profit"], race["place_profit"], race["lose_profit"] = calculate_profit(
        race["bookie_odds"],
        race["bookie_stake"],
        race["win_odds"],
        0,
        race["place_odds"],
        0,
        race["place_payout"],
    )
    race["bookie_balance"] = sporting_index.get_balance(driver)
    race["betfair_balance"] = betfair.get_balance()
    race["betfair_exposure"] = betfair.get_exposure()
    (
        race["exp_value"],
        race["exp_growth"],
        race["exp_return"],
    ) = calculate_expected_return(
        race["bookie_balance"] + race["betfair_balance"] + calc_unfinished_races(),
        race["win_odds"],
        race["place_odds"],
        race["win_profit"],
        race["place_profit"],
        race["lose_profit"],
    )
    output_punt(race)
    update_csv(race)
    alert_low_funds(race)


def scrape_races(driver, punt, lay):
    race = {
        "position": None,
        "bookie_balance": sporting_index.get_balance(driver),
        "betfair_balance": betfair.get_balance(),
    }
    if race["bookie_balance"] == 0:
        print("Sporting Index balance: 0")
        return
    processed_horses = []
    driver.switch_to.window(driver.window_handles[0])
    odds_monkey.refresh(driver)
    if not driver.find_elements_by_class_name("rgNoRecords"):
        for row in range(odds_monkey.get_no_rows(driver)):
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
            if lay and odds_monkey.available_to_lay(driver, row):
                if race["betfair_balance"] == 0:
                    print("Betfair balance: 0")
                else:
                    race.update(odds_monkey.find_races(driver, row))
                    evaluate_arb(driver, race)

            if punt and horse_name not in processed_horses:
                race.update(odds_monkey.find_races(driver, row))
                processed_horses.append(race["horse_name"])
                evaluate_punt(driver, race)

            driver.switch_to.window(driver.window_handles[0])
            driver.switch_to.default_content()
            sys.stdout.flush()


def start_matcher(driver, punt, lay):
    START_TIME = time()
    count = 0
    driver.switch_to.window(driver.window_handles[0])
    while True:
        loop_time = time()
        # So Sporting Index dosen't logout
        if count % 4 == 0:
            sporting_index.refresh(driver)
        if count % 10 == 0:
            show_info(count, START_TIME)

        scrape_races(driver, punt, lay)
        sys.stdout.flush()
        diff = time() - loop_time
        if diff < REFRESH_TIME:
            sleep(REFRESH_TIME - diff)
        count += 1


def run_each_way(punt, lay):
    if datetime.now().hour < 7:
        print("\nMatcher started too early (before 7am)")
        return
    print(f'Started at: {datetime.now().strftime("%H:%M:%S %d/%m/%Y")}')
    sys.stdout.flush()
    check_vars()
    while True:
        try:
            driver = setup_selenium()
            odds_monkey.login(driver)
            sporting_index.login(driver)
            start_matcher(driver, punt, lay)
        except MatcherError as e:
            print(e)
        except KeyboardInterrupt as e:
            print(e)
            break
        except WebDriverException as e:
            print()
            if "cannot activate web view" in str(e):
                print("WebDriver error occured: cannot activate web view")
            elif "chrome not reachable" in str(e):
                print("WebDriver error occured: chrome not reachable")
            elif "tab crashed" in str(e):
                print("WebDriver error occured: tab crashed")
            elif "cannot determine loading status" in str(e):
                print("WebDriver error occured: cannot determine loading status")
            else:
                print("Unknown WebDriver error occured: %s" % e)
                print(traceback.format_exc())
        except Exception as e:
            print("Unknown error occured: %s" % e)
            print(traceback.format_exc())
        finally:
            sys.stdout.flush()
            driver.quit()
