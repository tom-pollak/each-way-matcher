#!/bin/bash

cd $(cd -P -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
> debug.log
echo -e "\n" 2> /dev/null 3<backup.log 3<&- >>backup.log
git pull -q

xvfb-run -a python3 -m matcher | tee -a debug.log backup.log > /dev/null

git pull -q
python3 stats.py | tee -a debug.log backup.log > /dev/null
git commit -q -a -m "update returns" && git push -q
