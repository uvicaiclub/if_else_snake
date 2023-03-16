#!/bin/bash

solo_games=$1
robin_rounds=$2 # Number of rounds to play in robin robin tournament

function solo_if_else() {
    local rounds=$1
    for (( i = 0; i < $rounds; i++ )) 
    do
        ./battlesnake  play -g solo -n if_else -u http://localhost:8001 >/dev/null 2>&1
    done
}

function solo_sl_basic() {
    local rounds=$1
    for (( i = 0; i < $rounds; i++ )) 
    do
        ./battlesnake  play -g solo -n sl_basic -u http://localhost:8002 >/dev/null 2>&1
    done
}

function solo_sl_conv() {
    local rounds=$1
    for (( i = 0; i < $rounds; i++ )) 
    do
        ./battlesnake  play -g solo -n sl_conv -u http://localhost:8003 >/dev/null 2>&1
    done
}

# Run solo games for each snake
solo_if_else $solo_games &
solo_sl_basic $solo_games &
solo_sl_conv $solo_games &
wait

# Sleep for 20 seconds
#sleep 1

# Run each snake against each other snake
for (( i = 0; i < $robin_rounds; i++ )) 
do
    ./battlesnake  play -n roko3 -u http://localhost:8002 -n roko1 -u http://localhost:8002 -n roko2 -u http://localhost:8002 -n nobrain -u http://localhost:8002 >/dev/null 2>&1
    #./battlesnake  play -n roko -u http://localhost:8001 -n heu1 -u http://localhost:8003 -n heu2 -u http://localhost:8003 -n heu3 -u http://localhost:8003 >/dev/null 2>&1
    #./battlesnake  play -n sl_basic -u http://localhost:8002 -n sl_conv -u http://localhost:8003 >/dev/null 2>&1
    #./battlesnake  play -n sl_conv -u http://localhost:8003 -n if_else -u http://localhost:8001 >/dev/null 2>&1
done