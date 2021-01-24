#!/bin/bash

cd $(cd -P -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
git pull -q
python3 stats.py
git commit -q -a -m "update returns" && git push -q
