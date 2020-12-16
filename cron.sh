git pull
#Xvfb :99 -ac &
#export DISPLAY=:99
source ~/each-way-matcher/.env
xvfb-run -a python3 ~/each-way-matcher/run.py > debug.log
