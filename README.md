# Each Way Matcher

Scrapes OddsMonkey for profitable each way horse races, then automatically
places bets on
Sporting Index.  
Also lays arbitrage bets on Sporting Index and Betfair.

![balance graph](stats/balance.png)

## Login variables

### Create certificates + APP_KEY

- client-2048.crt/key [connected to the betfair api](https://docs.developer.betfair.com/display/1smk3cen4v3lu3yomq5qye0ni/Non-Interactive+%28bot%29+login#Non-Interactive(bot)login-LinkingtheCertificatetoYourBetfairAccount)
- [APP_KEY](https://support.developer.betfair.com/hc/en-us/articles/115003864651-How-do-I-get-started-)

### Add to .env

Sporting index: S_INDEX_USER S_INDEX_PASS  
Oddsmonkey (premium account): ODD_M_USER ODD_M_PASS  
Betfair: BETFAIR_USR BETFAIR_PASS APP_KEY

## Install

```bash
pip3 install -r requirements.txt
python3 -m matcher --setup
```

### Running headless

```bash
sudo apt install xvfb chromium-browser -y
```

Install the appropiate [chromedriver](https://chromedriver.chromium.org/downloads)
at default program location (/usr/bin/chromedriver for linux)

### Modify filters

Go to [each way matcher](https://www.oddsmonkey.com/Tools/Matchers/EachwayMatcher.aspx)

- Each Way Rating: 95 to 200
- SNR Rating, Normal Arb Rating, Back Odds: 0 to 200
- Event Start Time: Now to 7 days
- Sports: Horse Racing
- Markets: Horse Racing - Winner
- Bookmakers: Sporting Index only
- Exchanges: All exchanges
- Click save

## Run

```bash
python3 -m matcher --run
```

or

- Run with run.sh - uses xvfb to run selenium headless on a virtual screen and
logs output **(recommended)**
  - Can be run as a cron job or manually with ```./run.sh &``` in a tmux window
