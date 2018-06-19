#!/bin/bash
set -e
LONG_LOG=/var/log/pge_power_usage.log

cd $(dirname $0)

START_TIME=$(tail -1 $LONG_LOG | awk '{print $1}')

tfn=$(mktemp)
python3 pge.py $START_TIME > $tfn
cat $TFN >> $LONG_LOG

cat $tfn | while read a b; do echo "home.power_usage $b $(date -d $a +%s)"; done | nc -q0 localhost 2003
rm $tfn
