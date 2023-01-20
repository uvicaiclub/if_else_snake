# Given a game state, the predictor should return a list of 4 numbers, representing the probabilty of wining 
# if the snake moves up, down, left, or right, respectively.
# The predictor loads model.h5, which is a keras model that was trained on the data in trainingData.json.

import numpy as np
from tensorflow import keras
import typing
from copy import deepcopy

# Given game state, returns possible next game states
def get_next_states(game_state: typing.Dict) -> typing.List[typing.Dict]:
    head = game_state['you']['body'][0]
    next_bodies = [
        [{'x': head['x'], 'y': head['y']+1}],
        [{'x': head['x'], 'y': head['y']-1}],
        [{'x': head['x']-1, 'y': head['y']}],
        [{'x': head['x']+1, 'y': head['y']}]
    ]
    # If head out of bounds or colision set to False
    body_parts = [part for snake in game_state['board']['snakes'] for part in snake['body']]
    for i in range(len(next_bodies)):
        head = next_bodies[i]
        if (head[0]['x'] < 0 
            or head[0]['x'] >= game_state['board']['width'] 
            or head[0]['y'] < 0 
            or head[0]['y'] >= game_state['board']['height']):
            next_bodies[i] = False
        elif head[0] in body_parts:
            next_bodies[i] = False
    # Create resulting game states
    next_states = []
    for body in next_bodies:
        if body == False:
            next_states.append(False)
            continue
        for i in range(len(game_state['you']['body'][:-1])):
            body.append(game_state['you']['body'][i])
        next_state = deepcopy(game_state)
        next_state['you']['body'] = body
        for snake in next_state['board']['snakes']:
            if snake['name'] == '0':
                snake['body'] = body
        next_states.append(next_state)
    return next_states

class Predictor:
    def __init__(self):
        # Load model
        self.model = keras.models.load_model("snakeSupervision/trainedModel.h5")

    def predict(self, game_state: typing.Dict) -> typing.List[float]:
        board_width = game_state['board']['width']
        board_height = game_state['board']['height']
        # Get next states
        next_states = get_next_states(game_state)


        # Transform next states into nn input arrays
        nn_inputs = []
        for next_state in next_states:
            if next_state == False:
                nn_inputs.append(False)
                continue
            nn_input = np.zeros((board_width, board_height))
            for snake in next_state['board']['snakes']:
                for part in snake['body']:
                    if snake['name'] == '0':
                        nn_input[part['x']][part['y']] = 1
                    else:
                        nn_input[part['x']][part['y']] = -1
            for food in next_state['board']['food']:
                nn_input[food['x']][food['y']] = 2
            nn_input = nn_input.flatten()
            nn_input = nn_input.reshape(1, 121)
            nn_inputs.append(nn_input)

        """
        for i in range(len(nn_inputs[0])):
            if nn_inputs[0][0][i] != nn_inputs[1][0][i] or nn_inputs[0][0][i] != nn_inputs[2][0][i] or nn_inputs[0][0][i] != nn_inputs[3][0][i]:
                break
        else:
            print("All inputs are the same")"""

        # Predict probabilty of winning for each next state
        predictions = []
        for i in range(len(nn_inputs)):
            if type(nn_inputs[i]) is bool:
                predictions.append(0)
            else:
                predictions.append(self.model.predict(nn_inputs[i]))
        return predictions
