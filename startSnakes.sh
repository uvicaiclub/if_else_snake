python3 main.py 8001 "#ff0000" &
python3 main.py 8002 "#ffaaaa" &
python3 main.py 8003 "#00ff00" &
python3 main.py 8004 "#aaffaa" &
python3 main.py 8005 "#0000ff" &
python3 main.py 8006 "#aaaaff"

./battlesnake play -n one -u http://localhost:8001 -n two -u http://localhost:8002 -n three -u http://localhost:8003 -n four -u http://localhost:8004 -n five -u http://localhost:8005 -n six -u http://localhost:8006 --browser