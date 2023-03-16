# Given a game state, the predictor should return a list of 4 numbers, representing the probabilty of wining 
# if the snake moves up, down, left, or right, respectively.
# The predictor loads model.h5, which is a keras model that was trained on the data in trainingData.json.

import typing

import keras
import numpy as np


# Given a gamestate dict as returned by Battlesnake API, return a matrix that is rotated and 
# centered on the head of the snake indicated by the "you" dict.
# Implemented following code from make_state() in https://github.com/Fool-Yang/AlphaSnake-Zero/blob/master/code/utils/game.py
def gamestate_to_values(gamestate, subject_id):
    board = gamestate['board']

    # These values taken from the source, unsure on their significance
    HEAD_m = 0.04
    SNAKE_m = 0.02
    HEALTH_m = 0.01
    MY_HEAD = -1
    WALL = 1

    # Create the matrix to fill in from this game state
    n_channels = 3  # Channels: heads, obstacles (bodies & walls), food
    norm_width = board['width'] * 2 - 1
    norm_height = board['height'] * 2 - 1
    center_x = norm_width // 2
    center_y = norm_height // 2
    norm_matrix = np.zeros((3, norm_height, norm_width))

    # Get you
    you = {}
    for snake in board['snakes']:
        if snake['id'] == subject_id:
            you = snake
            break
    
    # Get your head position
    head_x = you['head']['x']
    head_y = you['head']['y']

    # Set center position value (this represents your head position)
    # Note: this value gets overwritten in channel 0, not sure what it's purpose is there
    norm_matrix[:, center_y, center_x] = MY_HEAD

    # For normalizing snake lengths, unsure on significance of the values used here
    length_minus_half = len(you['body']) - 0.5

    # Fill channels 0 & 1 with snake positions
    for snake in board['snakes']:
        # Get relative position of this head to your head
        head_rel_x = snake['head']['x'] - head_x
        head_rel_y = snake['head']['y'] - head_y

        # Normalize by length relative to you
        head_val = (len(snake['body']) - length_minus_half) * HEAD_m
        norm_matrix[0, center_y + head_rel_y, center_x + head_rel_x] = head_val

        # Now do the body positions (skip head)
        body = snake['body'][1:]
        dist = len(body)
        for position in body:
            body_rel_x = snake['body'][dist]['x'] - head_x
            body_rel_y = snake['body'][dist]['y'] - head_y
            norm_matrix[1, center_y + body_rel_y, center_x + body_rel_x] = dist*SNAKE_m
            # Track distance to tail (tail has dist = 1)
            dist -= 1

    # Fill channel 2 with food positions
    for food in board['food']:
        food_rel_x = food['x'] - head_x
        food_rel_y = food['y'] - head_y
        norm_matrix[2, center_y + food_rel_y, center_x + food_rel_x] = (101 - you['health']) * HEALTH_m

    # Fill in walls
    for x in range(norm_width):
        for y in range(norm_height):
            if (
                x < center_x - head_x 
                or x >= (center_x - head_x) + board['width']
                or y < center_y - head_y 
                or y >= (center_y - head_y) + board['height']
            ):
                norm_matrix[1, y, x] = WALL

    # Lastly, rotate the board so that we are "facing up"
    if len(you['body']) > 1:
        neck = you['body'][1]
        # Diagonals not possible, just check right, down, left
        if head_x > neck['x']:
            return np.rot90(norm_matrix, 3, (1,2)), 3
        elif head_y < neck['y']:
            return np.rot90(norm_matrix, 2, (1,2)), 2
        elif head_x < neck['x']:
            return np.rot90(norm_matrix, 1, (1,2)), 1
    # Either this is the first move (neck = head) or you are facing up (no rotation needed)
    return norm_matrix, 0


# Translate an action into a direction relative to the subject snake's head
def translate_action(board_height, board_width, action, num_rot):
    move_int = 0    # -1 = left, 0 = forward, 1 = right
    if action == 'up':
        if num_rot == 0:
            move_int = 0
        elif num_rot == 1:
            move_int = 1
        elif num_rot == 2:
            raise ValueError('Snake made suicidal move?')
        elif num_rot == 3:
            move_int = -1
    elif action == 'down':
        if num_rot == 0:
            raise ValueError('Snake made suicidal move?')
        elif num_rot == 1:
            move_int = -1
        elif num_rot == 2:
            move_int = 0
        elif num_rot == 3:
            move_int = 1
    elif action == 'left':
        if num_rot == 0:
            move_int = -1
        elif num_rot == 1:
            move_int = 0
        elif num_rot == 2:
            move_int = 1
        elif num_rot == 3:
            raise ValueError('Snake made suicidal move?')
    elif action == 'right':
        if num_rot == 0:
            move_int = 1
        elif num_rot == 1:
            raise ValueError('Snake made suicidal move?')
        elif num_rot == 2:
            move_int = -1
        elif num_rot == 3:
            move_int = 0
    return np.full((1, board_width, board_height), move_int)


class Predictor:
    def __init__(self, model_path: str):
        # Load model
        self.model = keras.models.load_model(f"snakeSupervision/{model_path}")
        self.model_path = model_path

    def predict(self, game_state: typing.Dict, action: str, subject: str):
        board_width = game_state['board']['width']
        board_height = game_state['board']['height']
        board_matrix, num_rot = gamestate_to_values(game_state, subject)
        actions_array = translate_action(
            board_height * 2 -1, 
            board_width * 2 -1, 
            action, num_rot
        )
        nn_inputs = np.concatenate((board_matrix, actions_array), axis=0)
        nn_inputs = np.transpose(nn_inputs, (1, 2, 0)).reshape(1, 21, 21, 4)

        # Predict probabilty of winning with this action
        prediction = (action, self.model(nn_inputs, training=False))
        return (prediction[0], float(prediction[1][0][0]))
