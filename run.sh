#!/bin/bash

cd $(cd -P -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
> debug.log
git pull -q

xvfb-run -a python3 main.py & 
wait
python3 stats.py

git pull -q && git commit -q -a -m "update returns" && git push -q
