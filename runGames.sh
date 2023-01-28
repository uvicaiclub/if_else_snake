#!/bin/bash
total_games=$1
batch_size=$2


for (( i = 0; i < $total_games; i = i + $batch_size ))
do
    echo "Trained $i games"
    for (( j = 0; j < $batch_size; j++ ))
    do
        # run the game, output to gamei.json
        ./battlesnake  play -n if_else -u http://localhost:8001 -n sl_snake -u http://localhost:8002 >/dev/null 2>&1
    done
    python3 parseGameData.py
    cd snakeSupervision
    python3 supervisor.py -m newConv_2.h5 2>/dev/null
    cd ..
    rm games/*
done