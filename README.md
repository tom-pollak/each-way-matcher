# Each Way Matcher

- Scrapes OddsMonkey for profitable each way horse races, then automatically
  places bets on
  Sporting Index.
- Lays arbitrage bets on Sporting Index and Betfair.

![graph](https://tom-pollak.github.io/each-way-matcher/balance.png)

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

## Login variables

### Create API keys + certificates

- client-2048.crt/key [connected to the betfair api](<https://docs.developer.betfair.com/display/1smk3cen4v3lu3yomq5qye0ni/Non-Interactive+%28bot%29+login#Non-Interactive(bot)login-LinkingtheCertificatetoYourBetfairAccount>) (put in git root directory)
- [APP_KEY](https://support.developer.betfair.com/hc/en-us/articles/115003864651-How-do-I-get-started-)
- [RAPID_API_KEY](https://rapidapi.com/ortegalex/api/horse-racing/) - sign up for free subsciption

### Create environmental variables

#### Copy .env.template to .env:

- Sporting index: S_INDEX_USER S_INDEX_PASS
- Oddsmonkey (premium account): ODD_M_USER ODD_M_PASS
- Betfair: BETFAIR_USR BETFAIR_PASS APP_KEY
- Horse results API key: RAPID_API_KEY

### Modify filters

Create a (premium) OddsMonkey account and go to [each way matcher](https://www.oddsmonkey.com/Tools/Matchers/EachwayMatcher.aspx)

- Each Way Rating: 98 to 200
- SNR Rating, Normal Arb Rating, Back Odds: 0 to 200
- Event Start Time: Now to 7 days
- Sports: Horse Racing
- Markets: Horse Racing - Winner
- Bookmakers: Sporting Index only
- Exchanges: Betfair and Smarkets
- Click save
- Go to settings, change betfair comission to 2%

## Run

```bash
python3 -m matcher --run
```

or

- Run with run.sh - uses xvfb to run selenium headless on a virtual screen and
  logs output **(recommended)**
  - Can be run as a cron job
  ```
  0 7 * * * [path to run.sh]
  @reboot [path to run.sh]
  ```
  - or manually with
  ```bash
  nohup ./run.sh >/dev/null 2>&1 &
  ```

You can view the help menu with

```bash
python3 -m matcher -h
```
