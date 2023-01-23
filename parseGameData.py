# This file parses battlesnake game data into a format that can be used for training a neural network.

import json
import os
import numpy as np

trainingExamples = open('snakeSupervision/trainingExamples.json', 'a')
trainingLabels = open('snakeSupervision/trainingLabels.json', 'a')

for filename in os.scandir('games/'):
    states_list = []
    actions_list = []
    winner = ''
    with open(filename) as game_data:
        next_line = game_data.readline()
        while next_line:
            line_dict = json.loads(next_line)
            if 'game' in line_dict:
                states_list.append(line_dict)
            elif 'winner' in line_dict:
                winner = line_dict['winner']
            else:
                actions_list.append(line_dict)
            next_line = game_data.readline()
    # For each state, actions pair create a training example for each snake as subject
    # Limit to last %10 of the game
    start_index = len(states_list) - len(states_list) // 10
    for state, actions in zip(states_list[start_index:], actions_list[start_index:]):
        board_width = state['board']['width']
        board_height = state['board']['height']
        for subject_snake in state['board']['snakes']:
            subject_id = subject_snake['id']
            if subject_id not in actions:
                continue
            subject_action = actions[subject_id]
            # Transform game state into nn input arrays
            subject_head = np.zeros((board_width, board_height))
            subject_body = np.zeros((board_width, board_height))
            heads_array = np.zeros((board_width, board_height))
            bodies_array = np.zeros((board_width, board_height))
            for snake in state['board']['snakes']:
                if snake['id'] == subject_id:
                    subject_head[snake['head']['x']][snake['head']['y']] = 1
                    for part in snake['body'][1:]:
                        subject_body[part['x']][part['y']] = 1
                else:
                    heads_array[snake['head']['x']][snake['head']['y']] = 1
                    for part in snake['body'][1:]:
                        bodies_array[part['x']][part['y']] = 1
            
            food_array = np.zeros((board_width, board_height))
            for food in state['board']['food']:
                food_array[food['x']][food['y']] = 1

            actions_array = np.zeros((4))
            if subject_action == 'up':
                actions_array[0] = 1
            elif subject_action == 'down':
                actions_array[1] = 1
            elif subject_action == 'left':
                actions_array[2] = 1
            elif subject_action == 'right':
                actions_array[3] = 1

            # Flatten arrays into 1D arrays
            subject_head = subject_head.flatten()
            subject_body = subject_body.flatten()
            heads_array = heads_array.flatten()
            bodies_array = bodies_array.flatten()
            food_array = food_array.flatten()
            actions_array = actions_array.flatten()

            final_array = np.concatenate((
                subject_head, subject_body, heads_array, bodies_array, food_array, actions_array
            ))
            json.dump(final_array.tolist(), trainingExamples)
            trainingExamples.write('\n')
            if subject_id == winner:
                trainingLabels.write('1')
            else:
                trainingLabels.write('0')