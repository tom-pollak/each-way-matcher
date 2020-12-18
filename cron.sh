git pull > /dev/null
xvfb-run -a python3 ~/each-way-matcher/run.py &> debug.log &
wait
./update_returns.sh
