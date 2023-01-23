# loop 100 times
x=0
while [ $x -le 5000 ]
do
    for i in {1..500}
    do
        # run the game, output to gamei.json
        ./battlesnake  play -n sl_snake1 -u http://localhost:8002 -n sl_snake2 -u http://localhost:8001 >/dev/null 2>&1
    done
    python3 parseGameData.py
    cd snakeSupervision
    python3 supervisor.py 2>/dev/null
    cd ..
    rm games/*
    x=$(( $x + 500 ))
    echo "Trained $x games"
done