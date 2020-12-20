cd ~/each-way-matcher
git pull > /dev/null
xvfb-run -a python3 run.py & #&> debug.log &
wait
#./update_returns.sh
