git pull > /dev/null
#Xvfb :99 -ac &
#export DISPLAY=:99
xvfb-run -a python3 ~/each-way-matcher/run.py > debug.log
