#!/bin/bash

kill -9 $(pidof python)
clear

for evs in `seq 0 1 $1`;   # num of evs
# for evs in `seq 10 1 $1`;   # num of evs
do
    for n in `seq 1 $2`; # num of runs
    # for n in `seq 4 1 $2`; # num of runs
    do

        echo ">>> Run #$n (evs$evs)"
        echo ">>> start $(date)"

        echo ">>> Cleaning mininet"
        sudo mn -c -v output

        echo ">>> Removing unecessary traffic"
        sudo systemctl disable avahi-daemon &> /dev/null
        sudo service avahi-daemon stop &> /dev/null

        echo ">>> Removing old logs"
        sudo rm -r logs/*

        # run experiment
        echo ">>> Running pox"
        python pox/pox.py forwarding.l2_learning_auth log.level --DEBUG > logs/pox.log 2>&1 &
        echo ">>> Running mininet..."
        sudo python scada_topo.py $evs > logs/mininet.log 2>&1

        # kill pox
        echo ">>> Killing pox"
        kill -9 $(pidof python)

        # cp logs
        echo ">>> Copying logs"
        mkdir -p experiments/evs$evs/$n/
        cp -r logs/* experiments/evs$evs/$n/
        echo ">>> done $(date)"

        echo
        echo

    done
done
