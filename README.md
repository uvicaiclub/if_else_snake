# if_else_snake
A simple battlesnake implemented with only decision. Template taken from [BattlesnakeOfficial/starter-snake-python](https://github.com/BattlesnakeOfficial/starter-snake-python)

## Installing Dependencies
Install dependencies using pip
```sh
pip install -r requirements.txt
```

## The Snakes
### Snake With  No brain
This snake performs very basic analysis on each turn to avoid taking actions that will lead to certain death. This analysis consists of three steps:

1. Avoid hitting it's own neck
2. Avoid hitting walls
3. Avoid hitting any snake's body

Once these actions have been removed, the snake then picks randomly from the remaining actions.

```sh
usage: main.py [-h] [-c COLOR] [-p PORT] [-d] [-s] [--stats_file STATS_FILE] [--print_level {1,2,3}]

optional arguments:
  -h, --help            show this help message and exit
  -c COLOR, --color COLOR
                        Hex color code. Default random.
  -p PORT, --port PORT  Port to run Battlesnake on. Default 8001.
  -d, --deployed        Opens server to the internet
  -s, --save_games      Save game data to file for training
  --stats_file STATS_FILE
                        Path to store game stats
  --print_level {1,2,3}
                        1: silence all prints 2: (Default) silence move(), info(), start() 3: print from all endpoints
```


# Snake With A Brain
This snake performs the exact same analysis as Snake With No Brain. However, instead of chosing randomly from the non-certain-death moves, it uses a nueral network to rank the remaining actions and picks the best one.


```sh
usage: sl_snake.py [-h] [-c COLOR] [-p PORT] [-d] [-s] [-m MODEL] [--stats_file STATS_FILE] [--print_level {1,2,3}]

optional arguments:
  -h, --help            show this help message and exit
  -c COLOR, --color COLOR
                        Hex color code. Default random.
  -p PORT, --port PORT  Port to run Battlesnake on. Default 8001.
  -d, --deployed        Opens server to the internet
  -s, --save_games      Save game data to file for training
  -m MODEL, --model MODEL
                        Filename of model to use for predictions. Default basicModel.h5
  --stats_file STATS_FILE
                        Path to store game stats
  --print_level {1,2,3}
                        1: silence all prints 2: (Default) silence move(), info(), start() 3: print from all endpoints
```


## Play a Game Locally

Install the [Battlesnake CLI](https://github.com/BattlesnakeOfficial/rules/tree/main/cli)
* You can [download compiled binaries here](https://github.com/BattlesnakeOfficial/rules/releases)
* or [install as a go package](https://github.com/BattlesnakeOfficial/rules/tree/main/cli#installation) (requires Go 1.18 or higher)

Command to run a local game

```sh
battlesnake play -W 11 -H 11 --name 'Python Starter Project' --url http://localhost:8000 -g solo --browser
```