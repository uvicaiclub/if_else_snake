for i in {1..100}
do
    # run the game, output to gamei.json
    ./battlesnake  play -n basic -u http://localhost:8002 -n if_else -u http://localhost:8001
done