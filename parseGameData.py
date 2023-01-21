# This file parses battlesnake game data into a format that can be used for training a neural network.

import json

games = []
for i in range(1, 101):
    game = {"turns": [], 'winner': 0}
    with open(f"games/game{i}.json", "r") as gamefile:
        lines = [json.loads(line) for line in gamefile.readlines()]
        if lines[-1]['isDraw']:
            game['winner'] = -1
        else:
            game['winner'] = int(lines[-1]['winnerName'])
        for turn in lines[1:-1]:
            turnArray = [[0] * turn['board']['height'] for i in range(turn['board']['width'])]
            for snake in turn['board']['snakes']:
                for part in snake['body']:
                    turnArray[part['x']][part['y']] = int(snake['name'])
            for food in turn['board']['food']:
                assert turnArray[food['x']][food['y']] == 0
                turnArray[food['x']][food['y']] = 3
            game['turns'].append(turnArray)
    games.append(game)

# Write training data to file
with open("trainingData.json", "w") as trainFile:
    trainFile.write(json.dumps(games))
