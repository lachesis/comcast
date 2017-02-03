#!/bin/bash
set -e
LONG_LOG=/var/log/comcast_data_usage.log

cd $(dirname $0)

send_stats () {
    # usage: send_stats $name $value $target_unit
    if [[ "$3" == "" ]]; then
        conv=$2
    else
        conv=$(units -o "%.0f" -t "$2" "$3")
    fi
    echo "comcast.usage.$1:$conv|g" | ncat -u -4 -w 2 -i 2 localhost 8125
}

tfn=$(mktemp)
python3 comcast.py > $tfn
jq -c . $tfn >> $LONG_LOG

used=$(jq -r '.used' $tfn)
total=$(jq -r '.total' $tfn)
unit=$(jq -r '.unit' $tfn)

[[ "$unit" == "MB" ]] && unit="MiB"
[[ "$unit" == "GB" ]] && unit="GiB"
[[ "$unit" == "TB" ]] && unit="TiB"

echo $used $unit of $total $unit

send_stats 'used' "$used $unit" "bytes"
send_stats 'total' "$total $unit" "bytes"

rm $tfn
