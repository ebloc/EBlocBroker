#!/bin/bash

#nohup python -u test.py >/dev/null 2>&1 # Output will be logged on clientOutput.txt
nohup python -u testEudat.py & #>/dev/null 2>&1

if [ "$1" == "" ]; then
    sudo tail -f nohup.out
fi

