#!/bin/bash

function solo_if_else() {
    for i in {1..50}
    do
        ./battlesnake  play -g solo -n if_else -u http://localhost:8001
    done
}

function solo_sl_basic() {
    for i in {1..50}
    do
        ./battlesnake  play -g solo -n sl_basic -u http://localhost:8002
    done
}

function solo_sl_conv() {
    for i in {1..50}
    do
        ./battlesnake  play -g solo -n sl_conv -u http://localhost:8003
    done
}

# Run solo games for each snake
solo_if_else &
solo_sl_basic &
solo_sl_conv &
wait

# Run each snake against each other snake
for i in {1..50}
do
    ./battlesnake  play -n if_else -u http://localhost:8001 -n sl_basic -u http://localhost:8002
    ./battlesnake  play -n sl_basic -u http://localhost:8002 -n sl_conv -u http://localhost:8003
    ./battlesnake  play -n sl_conv -u http://localhost:8003 -n if_else -u http://localhost:8001
done