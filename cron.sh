git pull
sudo pkill Xvfb
Xvfb :99 -ac &
export DISPLAY=:99
source ~/each-way-matcher/.env
python3 ~/each-way-matcher/run.py
