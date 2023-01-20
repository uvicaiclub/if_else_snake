# loop 100 times
for i in {2001..2200}
do
    # run the game, output to gamei.json
    ./battlesnake  play -n 0 -u http://localhost:8001 -n 1 -u http://localhost:8002 -o games/game$i.json
done