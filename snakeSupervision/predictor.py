# Given a game state, the predictor should return a list of 4 numbers, representing the probabilty of wining 
# if the snake moves up, down, left, or right, respectively.
# The predictor loads model.h5, which is a keras model that was trained on the data in trainingData.json.

import numpy as np
from tensorflow import keras
import typing
from copy import deepcopy


class Predictor:
    def __init__(self):
        # Load model
        self.model = keras.models.load_model("snakeSupervision/trainedModel.h5")

    def predict(self, game_state: typing.Dict, action: str) -> typing.Tuple(str, float):
        board_width = game_state['board']['width']
        board_height = game_state['board']['height']

        # Transform game state into nn input array
        snake_bodies = []
        for snake in game_state['board']['snakes']:
            body_array = np.zeros((board_width, board_height))
            for part in snake['body']:
                body_array[part['x']][part['y']] = 1
            snake_bodies.append(body_array)
        
        snake_heads = []
        for snake in game_state['board']['snakes']:
            head_array = np.zeros((board_width, board_height))
            head_array[snake['head']['x']][snake['head']['y']] = 1
            snake_heads.append(head_array)

        food_array = np.zeros((board_width, board_height))
        for food in game_state['board']['food']:
            food_array[food['x']][food['y']] = 1

        actions_array = np.zeros((4))
        if action == 'up':
            actions_array[0] = 1
        elif action == 'down':
            actions_array[1] = 1
        elif action == 'left':
            actions_array[2] = 1
        elif action == 'right':
            actions_array[3] = 1

        # Flatten arrays into 1D arrays
        snake_bodies = np.array(snake_bodies).flatten()
        snake_heads = np.array(snake_heads).flatten()
        food_array = food_array.flatten()
        actions_array = actions_array.flatten()

        # Combine arrays into one nn input array
        nn_inputs = np.concatenate((snake_bodies, snake_heads, food_array, actions_array))

        # Predict probabilty of winning with this action
        return (action, self.model.predict(nn_inputs))
