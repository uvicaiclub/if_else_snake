# Given a game state, the predictor should return a list of 4 numbers, representing the probabilty of wining 
# if the snake moves up, down, left, or right, respectively.
# The predictor loads model.h5, which is a keras model that was trained on the data in trainingData.json.

import numpy as np
import keras
import typing
from copy import deepcopy


class Predictor:
    def __init__(self, model_path: str):
        # Load model
        self.model = keras.models.load_model(f"snakeSupervision/{model_path}")

    def predict(self, game_state: typing.Dict, action: str, subject: str):
        board_width = game_state['board']['width']
        board_height = game_state['board']['height']

        # Transform game state into nn input arrays
        subject_head = np.zeros((board_width, board_height))
        subject_body = np.zeros((board_width, board_height))
        heads_array = np.zeros((board_width, board_height))
        bodies_array = np.zeros((board_width, board_height))
        for snake in game_state['board']['snakes']:
            if snake['id'] == subject:
                subject_head[snake['head']['x']][snake['head']['y']] = 1
                for part in snake['body'][1:]:
                    subject_body[part['x']][part['y']] = 1
            else:
                heads_array[snake['head']['x']][snake['head']['y']] = 1
                for part in snake['body'][1:]:
                    bodies_array[part['x']][part['y']] = 1

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
        subject_head = subject_head.flatten()
        subject_body = subject_body.flatten()
        heads_array = heads_array.flatten()
        bodies_array = bodies_array.flatten()
        food_array = food_array.flatten()
        actions_array = actions_array.flatten()

        # Combine arrays into one nn input array
        nn_inputs = np.concatenate((
            subject_head, subject_body, heads_array, bodies_array, food_array, actions_array
        )).reshape(1, 609)
        # Predict probabilty of winning with this action
        prediction = (action, self.model(nn_inputs, training=False))
        return (prediction[0], float(prediction[1][0][0]))
