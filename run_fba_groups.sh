#!/usr/bin/env bash

./stop_all.sh
groups=$1
flag=$3
timestamp=$(date +'%Y-%m-%d_%H:%M:%S')
interval=$2
if [ -z "$2" ]
then
	interval=3
fi

if [ -z "$1" ];
then
	groups=1
fi

for i in `seq $groups`;
do
	websockify 800$i localhost:1200$i &
	python3 run_exchange_server.py --host localhost --port 1200$i --mechanism fba --interval $interval  --book_log FBA_DATA/${timestamp}_group_$i.log --${flag} & 

done
