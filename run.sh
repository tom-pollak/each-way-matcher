cd ~/each-way-matcher
git pull -q
xvfb-run -a python3 run.py & 
wait
./update_returns.sh &> /dev/null
