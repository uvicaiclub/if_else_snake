#!/bin/bash
total_games=$1
batch_size=$2


for (( i = 0; i < $total_games; i = i + $batch_size ))
do
    echo "Trained $i games"
    for (( j = 0; j < $batch_size; j++ ))
    do
        # run the game, output to gamei.json
        ./battlesnake  play -n if_else -u http://localhost:8002 -n sl_snake -u http://localhost:8001 >/dev/null 2>&1
    done
    echo "Parsing games"
    python3 parseGameData.py
    cd snakeSupervision
    python3 supervisor.py 2>/dev/null
    cd ..
    rm games/*
done