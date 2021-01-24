#!/bin/bash

cd $(cd -P -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
> debug.log
git pull -q

xvfb-run -a python3 main.py | tee -a debug.log backup.log > /dev/null &
wait

git pull -q
python3 stats.py | tee -a debug.log backup.log > /dev/null
git commit -q -a -m "update returns" && git push -q
