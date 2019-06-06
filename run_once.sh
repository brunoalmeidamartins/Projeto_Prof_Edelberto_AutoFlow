#!/bin/bash

clear

evs=$1

echo ">>> Running with $evs EV(s)"
echo

killall python
echo ">>> Cleaning mininet"
sudo mn -c -v output

echo ">>> Removing DNS"
sudo systemctl disable avahi-daemon &> /dev/null
sudo service avahi-daemon stop &> /dev/null

# run experiment
echo ">>> Removing logs"
sudo rm -r logs/*
# python pox/pox.py forwarding.l2_learning_auth log.level --DEBUG log --file=logs/pox.log &
echo ">>> Running pox"
python pox/pox.py forwarding.l2_learning_auth log.level --DEBUG > logs/pox.log 2>&1 &
echo ">>> Running mininet"
sudo python scada_topo.py $evs > logs/mininet.log 2>&1

# kill pox
echo ">>> Killing pox"
killall python
