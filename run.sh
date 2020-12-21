cd ~/each-way-matcher
git pull > /dev/null
xvfb-run -a python3 run.py & 
wait
./update_returns.sh > /dev/null
