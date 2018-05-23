#!/bin/bash

if [ "$#" -ne 1 ]; then
        echo "usage: ./run_cda_groups.sh [num_groups]"
        exit 1
fi

groups=$1
timestamp=$(date +'%Y-%m-%d_%H:%M:%S')
flag=$2

./stop_all.sh


for i in `seq $groups`;
do
	mkdir CDA_DATA i  > /dev/null 2> /dev/null
	python3 run_exchange_server.py --host localhost --port 900$i --mechanism cda --book_log CDA_DATA/${timestamp}_group_$i.log 
done
