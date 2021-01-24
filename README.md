# Each way matcher

Scrapes OddsMonkey for profitable each way horse races, then automatically
places bets on
Sporting Index.  
Also lays arbitrage bets on Sporting Index and Betfair.

## Login variables

### Add to .env

Sporting index: S_INDEX_USER S_INDEX_PASS  
Oddsmonkey (premium account): ODD_M_USER ODD_M_PASS  
Betfair: BETFAIR_USR BETFAIR_PASS APP_KEY

### Create certificates

client-2048.pub/key [connected to the betfair api](https://docs.developer.betfair.com/display/1smk3cen4v3lu3yomq5qye0ni/Non-Interactive+%28bot%29+login#Non-Interactive(bot)login-LinkingtheCertificatetoYourBetfairAccount)

## Install

```bash
sudo apt-get install xvfb -y
pip install -r requirements.txt
```

Install the latest chrome or chromium browser with the appropiate
[chromedriver](https://chromedriver.chromium.org/downloads) at default program
location (/usr/bin/chromedriver for linux)

## Run

```bash
python3 main.py
```

or

- Run with run.sh - uses xvfb to run selenium headless on a virtual screen and
logs output
  - Can be run as a cron job or manually with ```./run.sh &``` in a tmux window
