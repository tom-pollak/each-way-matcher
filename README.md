# each-way-betbot

Scrapes OddsMonkey for profitable each way horse races, automatically bets on
sporting index

Add S_INDEX_USER S_INDEX_PASS ODD_M_USER ODD_M_PASS to .env for sporting index betting
also add BETFAIR_USR BETFAIR_PASS APP_KEY for betfair api

```python
pipenv shell
pipenv install -r requirements.txt
python run.py
```

or run run.ps1 with a task scheduler
