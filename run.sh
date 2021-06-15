#!/bin/bash

cd "$(cd -P -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
> debug.log
echo -e "\n" 2> /dev/null 3<backup.log 3<&- >>backup.log
git pull -q

xvfb-run -a python3 -m matcher -rplsg | tee -a debug.log backup.log

cd stats
git commit -q -a -m "update returns" && git push -q
