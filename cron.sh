#!/bin/bash

cd $(cd -P -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
 run.sh | tee -a debug.log backup.log > /dev/null
