# This file parses battlesnake game data into a format that can be used for training a neural network.

import json

training_examples = []
training_labels = []
for i in range(1, 2201):
    with open(f"games/game{i}.json", "r") as gamefile:
        lines = [json.loads(line) for line in gamefile.readlines()]
        if lines[-1]['isDraw']:
            continue
        for turn in lines[1:-1]:
            turnArray = [[0] * turn['board']['height'] for i in range(turn['board']['width'])]
            for snake in turn['board']['snakes']:
                for part in snake['body']:
                    if snake['name'] == '0':
                        turnArray[part['x']][part['y']] = 1
                    else:
                        turnArray[part['x']][part['y']] = -1
            for food in turn['board']['food']:
                assert turnArray[food['x']][food['y']] == 0
                turnArray[food['x']][food['y']] = 2
            flatArray = [item for sublist in turnArray for item in sublist]
            training_examples.append(flatArray)
            if int(lines[-1]['winnerName']) == 0:
                training_labels.append(1)
            else:
                training_labels.append(0)
# Write training data to file
with open("trainingExamples.json", "w") as trainFile:
    trainFile.write(json.dumps(training_examples))
with open("trainingLabels.json", "w") as lableFile:
    lableFile.write(json.dumps(training_labels))
