# Each way matcher

Scrapes OddsMonkey for profitable each way horse races, automatically bets on
sporting index.

Can also lay arbritage bets on sporting index and betfair.

Add S_INDEX_USER S_INDEX_PASS ODD_M_USER ODD_M_PASS  to .env for sporting index betting
also add BETFAIR_USR BETFAIR_PASS APP_KEY and a certificate client-2048.pub/key connected to the betfair api

```bash
pip install -r requirements.txt
python main.py
```

or run with run.sh or as a cron job with cron.sh
