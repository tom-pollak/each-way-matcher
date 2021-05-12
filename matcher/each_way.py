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
    calcualte_stakes_from_profit,
    calculate_expected_return,
    kelly_criterion,
    minimize_loss,
    check_stakes,
    check_odds,
    maximize_arb,
    check_start_time,
)
from .stats import check_repeat_bets
from .output import (
    update_csv,
    show_info,
    ouput_lay,
    output_punt,
)
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
    bet_info.update(betfair.get_bets_by_bet_id(lay_win["bet_id"], lay_place["bet_id"]))
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
        betfair.cancel_unmatched_bets()
        win_odds = betfair.get_odds(market_ids["win"])[horse_name]["lay_odds_1"]
        place_odds = betfair.get_odds(market_ids["place"])[horse_name]["lay_odds_1"]
        betfair_balance = betfair.get_balance()
        win_stake, place_stake = minimize_loss(
            win_odds, place_odds, profits, betfair_balance, place_payout
        )
        if not check_stakes(
            0,
            betfair_balance,
            0,
            win_stake,
            win_odds,
            place_stake,
            place_odds,
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
    eval_start = time()  # debug
    if not check_start_time(race, mins=1):
        return
    race["bet_type"] = "Arb"
    race["betfair_balance"] = betfair.get_balance()
    (
        stakes_ok,
        race["bookie_stake"],
        race["win_stake"],
        race["place_stake"],
    ) = calculate_stakes(
        race["bookie_balance"],
        race["betfair_balance"],
        race["bookie_stake"],
        race["win_stake"],
        race["win_odds"],
        race["place_stake"],
        race["place_odds"],
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
        race["bet_type"] = "Lay Punt"
        bet_types, _ = check_repeat_bets(
            race["horse_name"], race["date_of_race"], race["venue"]
        )
        if "Lay Punt" in bet_types:
            return
        stake_proportion = maximize_arb(
            race["bookie_balance"],
            race["betfair_balance"],
            race["win_odds"],
            race["place_odds"],
            *profits,
        )
        race["bookie_stake"] = round(race["bookie_stake"] * stake_proportion, 2)
        race["win_stake"] = round(race["win_stake"] * stake_proportion, 2)
        race["place_stake"] = round(race["place_stake"] * stake_proportion, 2)
        stakes_ok = check_stakes(
            race["bookie_balance"],
            race["betfair_balance"],
            race["bookie_stake"],
            race["win_stake"],
            race["win_odds"],
            race["place_stake"],
            race["place_odds"],
        )
        if not stakes_ok:
            print(f"Arb bet not profitable: {profits} - {stake_proportion}")
            return

    market_ids, selection_id, got_race, race["horse_name"] = betfair.get_race_ids(
        race["date_of_race"], race["venue"], race["horse_name"]
    )
    if not got_race:
        print("Couldn't get race")
        return

    win_horse_odds = betfair.get_odds(market_ids["win"])
    place_horse_odds = betfair.get_odds(market_ids["place"])
    if not check_odds(race, win_horse_odds, place_horse_odds):
        try:
            race["win_odds"] = win_horse_odds[race["horse_name"]]["lay_odds_1"]
            race["place_odds"] = place_horse_odds[race["horse_name"]]["lay_odds_1"]
        except KeyError:
            print(
                f"{race['horse_name']} not in horse odds:\n{win_horse_odds}\n{place_horse_odds}"
            )
            return
        evaluate_arb(driver, race)
        return

    print("up to place arb took", time() - eval_start)  # debug
    race, bet_made = sporting_index.make_bet(driver, race, market_ids, lay=True)
    if bet_made is None:
        print(
            f"Horse not found: {race['horse_name']}  venue: {race['venue']}  race time: {race['date_of_race']}"
        )
    elif not bet_made:
        return

    place_arb_start = time()  # debug
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
    print("betfair bet took", time() - place_arb_start)  # debug

    race["win_odds"] = betfair.get_odds(market_ids["win"])[race["horse_name"]][
        "lay_odds_1"
    ]
    race["place_odds"] = betfair.get_odds(market_ids["place"])[race["horse_name"]][
        "lay_odds_1"
    ]
    race["win_stake"], race["place_stake"] = calcualte_stakes_from_profit(
        race["place_profit"],
        race["lose_profit"],
        race["bookie_stake"],
        race["bookie_odds"],
        race["place_odds"],
        race["place_payout"],
    )
    (
        race["exp_value"],
        race["exp_growth"],
        race["exp_return"],
    ) = calculate_expected_return(
        race["bookie_balance"] + race["betfair_balance"],
        race["win_odds"],
        race["place_odds"],
        race["win_profit"],
        race["place_profit"],
        race["lose_profit"],
    )
    race["betfair_balance"] = betfair.get_balance()
    race["bookie_balance"] = sporting_index.get_balance(driver)
    race["betfair_exposure"] = betfair.get_exposure()
    (
        race["exp_value"],
        race["exp_growth"],
        race["exp_return"],
    ) = calculate_expected_return(
        race["bookie_balance"] + race["betfair_balance"],
        race["win_odds"],
        race["place_odds"],
        race["win_profit"],
        race["place_profit"],
        race["lose_profit"],
    )

    ouput_lay(race)
    update_csv(race)


def scrape_arb_races(driver):
    race = {"bookie_balance": sporting_index.get_balance(driver)}
    processed_horses = []
    driver.switch_to.window(driver.window_handles[2])
    odds_monkey.refresh(driver, betfair=True)
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
            if horse_name not in processed_horses:
                race.update(odds_monkey.find_races(driver, row, 2))
                processed_horses.append(race["horse_name"])
                evaluate_arb(driver, race)
            driver.switch_to.window(driver.window_handles[2])
            driver.switch_to.default_content()
            sys.stdout.flush()


def evaluate_punt(driver, race):
    _, _, _, race["horse_name"] = betfair.get_race_ids(
        race["date_of_race"], race["venue"], race["horse_name"]
    )
    bet_types, win_odds_proportion = check_repeat_bets(
        race["horse_name"], race["date_of_race"], race["venue"]
    )
    if "Punt" in bet_types:
        return

    race["bookie_stake"] = kelly_criterion(
        race["bookie_odds"],
        race["win_odds"] * win_odds_proportion,
        race["place_odds"],
        race["place_payout"],
        race["bookie_balance"],
    )

    if race["bookie_stake"] < 0.1:
        return

    sporting_index_start = time()  # debug
    race, bet_made = sporting_index.make_bet(driver, race)
    if bet_made is None:  # horse not found
        print(
            f"Horse not found: {race['horse_name']}  venue: {race['venue']}  race time: {race['date_of_race']}"
        )
        return
    if not bet_made:
        return
    print("punt sporting index bet took", time() - sporting_index_start)  # debug
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
    (
        race["exp_value"],
        race["exp_growth"],
        race["exp_return"],
    ) = calculate_expected_return(
        race["bookie_balance"] + race["betfair_balance"],
        race["win_odds"],
        race["place_odds"],
        race["win_profit"],
        race["place_profit"],
        race["lose_profit"],
    )
    race["betfair_exposure"] = betfair.get_exposure()
    race["win_stake"] = race["place_stake"] = 0
    output_punt(race)
    update_csv(race)


def scrape_punt_races(driver):
    race = {"bookie_balance": sporting_index.get_balance(driver), "bet_type": "Punt"}
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
            if horse_name not in processed_horses:
                race.update(odds_monkey.find_races(driver, row, 0))
                processed_horses.append(race["horse_name"])
                evaluate_punt(driver, race)

            driver.switch_to.window(driver.window_handles[0])
            driver.switch_to.default_content()
            sys.stdout.flush()


def start_matcher(driver, lay):
    START_TIME = time()
    sporting_index.setup(driver)
    odds_monkey.open_betfair_page(driver)
    count = 0
    driver.switch_to.window(driver.window_handles[0])
    while True:
        loop_time = time()
        # So sporting index dosent logout
        if count % 4 == 0:
            sporting_index.refresh(driver)
        if count % 10 == 0:
            show_info(count, START_TIME)

        if lay:
            scrape_arb_races(driver)
        scrape_punt_races(driver)
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
    sys.stdout.flush()
    check_vars()
    while True:
        try:
            driver = setup_selenium()
            odds_monkey.login(driver)
            sporting_index.login(driver)
            start_matcher(driver, lay)
        except MatcherError as e:
            print(e)
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
