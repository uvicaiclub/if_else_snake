# loop 100 times
for i in {1..100}
do
    # run the game, output to gamei.json
    ./battlesnake  play -n 1 -u http://localhost:8001 -n 2 -u http://localhost:8002 -o games/game$i.json
done