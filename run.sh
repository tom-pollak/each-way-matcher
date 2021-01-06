cd ~/each-way-matcher
> debug.log
git pull -q
xvfb-run -a python3 main.py & 
wait
./update_returns.sh
