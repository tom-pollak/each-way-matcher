# Each way matcher

Scrapes OddsMonkey for profitable each way horse races, automatically bets on
sporting index.  
Also lays arbritage bets on sporting index and betfair.

## Login variables

### Add to .env

Sporting index: S_INDEX_USER S_INDEX_PASS  
Oddsmonkey (premium account): ODD_M_USER ODD_M_PASS  
Betfair: BETFAIR_USR BETFAIR_PASS APP_KEY

### Create certificates
client-2048.pub/key [connected to the betfair api](https://docs.developer.betfair.com/display/1smk3cen4v3lu3yomq5qye0ni/Non-Interactive+%28bot%29+login#Non-Interactive(bot)login-LinkingtheCertificatetoYourBetfairAccount)

## Install

```bash
pip install -r requirements.txt
```

## Run

```bash
python3 main.py
```

or
- run with run.sh
- use cron.sh in a cron job or to write to output to log files (recommended)
