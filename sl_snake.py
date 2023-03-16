# Welcome to
# __________         __    __  .__                               __
# \______   \_____ _/  |__/  |_|  |   ____   ______ ____ _____  |  | __ ____
#  |    |  _/\__  \\   __\   __\  | _/ __ \ /  ___//    \\__  \ |  |/ // __ \
#  |    |   \ / __ \|  |  |  | |  |_\  ___/ \___ \|   |  \/ __ \|    <\  ___/
#  |________/(______/__|  |__| |____/\_____>______>___|__(______/__|__\\_____>
#
# This file can be a nice home for your Battlesnake logic and helper functions.
#
# To get you started we've included code to prevent your Battlesnake from moving backwards.
# For more info see docs.battlesnake.com

import argparse
import json
import random
import typing

parser = argparse.ArgumentParser()
parser.add_argument('-c', '--color',
default=random.choice(["#DFFF00","#FFBF00","#FF7F50","#DE3163","#9FE2BF","#40E0D0","#6495ED","#CCCCFF"]),
help='Hex color code. Default random.')
parser.add_argument('-p', '--port', default='8001',
help='Port to run Battlesnake on. Default 8001.')
parser.add_argument('-d', '--deployed', action='store_true',
help='Opens server to the internet')
parser.add_argument('-s', '--save_games', action='store_true',
help='Save game data to file for training')
parser.add_argument('-m', '--model', default='convModel.h5',
help='Filename of model to use for predictions. Default convModel.h5')
parser.add_argument('--print_level', default=2, type=int, choices=[1,2,3],
    help='''1: silence all prints
            2: (Default) silence move(), info(), start()
            3: print from all endpoints'''
)
args = parser.parse_args()

from snakeSupervision.predictor import Predictor

predictor  = Predictor(args.model)
# Game stats
stats = {
    'games': 0,
    'wins': 0,
    'losses': 0,
    'sizes': [],
    'turns': []
}
# To handle multiple instance of this snake in the same game
# Indexed as ongoing_games[game_id][snake_id] = [body_length, turns_survived]
ongoing_games = {}

# info is called when you create your Battlesnake on play.battlesnake.com
# and controls your Battlesnake's appearance
# TIP: If you open your Battlesnake URL in a browser you should see this data
def info() -> typing.Dict:
    return {
        "apiversion": "1",
        "author": "me",  # TODO: Your Battlesnake Username
        "color": args.color,
        "head": "cosmic-horror",
        "tail": "mystic-moon",
    }


# start is called when your Battlesnake begins a game
def start(game_state: typing.Dict):
    # Initialize game stats
    global ongoing_games
    if game_state['game']['id'] not in ongoing_games:
        ongoing_games[game_state['game']['id']] = {}
    ongoing_games[game_state['game']['id']][game_state['you']['id']] = [len(game_state['you']['body']), 0]


# Given a game state, perform common preprocessing and return results
def preprocess(game_state: typing.Dict):
    # Create obstacles array storing each body part's expected lifetime
    obstacles = [
        [0] * game_state['board']['height']
        for x in range(game_state['board']['width'])
    ]
    for snake in game_state['board']['snakes']:
        snake_length = len(snake['body'])
        for i, body_part in enumerate(snake['body'][:-1]):
            # Store distance of body part to it's own tail
            # If snake just ate, tail pos is 1 otherwise it is 0
            obstacles[body_part['x']][body_part['y']] = snake_length - (i + 1)
    return obstacles


def get_previous_actions(game_state: typing.Dict)-> typing.Dict:
    previous_actions = {}
    for snake in game_state['board']['snakes']:
        previous_actions[snake['id']] = get_action(snake['body'][1], snake['head'])
    return previous_actions


def get_action(from_pos: typing.Dict, to_pos: typing.Dict)-> str:
    if to_pos['y'] > from_pos['y']:
        return 'up'
    elif to_pos['y'] < from_pos['y']:
        return 'down'
    elif to_pos['x'] > from_pos['x']:
        return 'right'
    elif to_pos['x'] < from_pos['x']:
        return 'left'


# Given head position and direction, return the new head position
def get_move_position(head: typing.Dict, direction: str)-> typing.Dict:
    if direction == 'up':
        return {'y': head['y']+1, 'x': head['x']}
    elif direction == 'down':
        return {'y': head['y']-1, 'x': head['x']}
    elif direction == 'left':
        return {'x': head['x']-1, 'y': head['y']}
    elif direction == 'right':
        return {'x': head['x']+1, 'y': head['y']}


# Given game state, head position, and current move risks, determines fatal out-of-bounds moves
# returns updated move risks
def avoid_walls(game_state: typing.Dict, head_pos: typing.Dict, danger_risk: typing.Dict) -> typing.Dict:
    # Left wall is at x = -1, don't go there
    if head_pos['x'] == 0:
        danger_risk['left'] += 1
    # Right wall is at x = board_width, don't go there
    elif head_pos['x'] == game_state['board']['width']-1:
        danger_risk['right'] += 1
    # Bottom wall is at y = -1, don't go there
    if head_pos['y'] == 0:
        danger_risk['down'] += 1
    # Top wall is at y = board_height, don't go there
    elif head_pos['y'] == game_state['board']['height']-1:
        danger_risk['up'] += 1
    return danger_risk


# Given obstacles array, head position & current move risk, determines moves that will be fatal colision
# with any snake body. Returns updated move risk.
def avoid_snake_bodies(obstacles: list, head_pos: typing.Dict, danger_risk: typing.Dict) -> typing.Dict:
    for move in danger_risk:
        mov_pos = get_move_position(head_pos, move)
        # Ensure that move is in bounds
        if mov_pos['x'] >= 0 and mov_pos['x'] < len(obstacles):
            if mov_pos['y'] >= 0 and mov_pos['y'] < len(obstacles[0]):
                # If an obstacle is at move position, add 1 to risk
                if obstacles[mov_pos['x']][mov_pos['y']] > 0:
                    danger_risk[move] += 1
    return danger_risk


# move is called on every turn and returns your next move
# Valid moves are "up", "down", "left", or "right"
# See https://docs.battlesnake.com/api/example-move for available data
def move(game_state: typing.Dict) -> typing.Dict:
    global ongoing_games
    ongoing_games[game_state['game']['id']][game_state['you']['id']] = [
        len(game_state['you']['body']),
        game_state['turn']
    ]
    # Record actions taken by each snake in previous turn and write to file
    if game_state['turn'] > 0 and args.save_games:
        previous_actions = get_previous_actions(game_state)
        with open(f"games/{game_state['game']['id']}.json", "a") as fp:
            json.dump(previous_actions, fp)
            fp.write('\n')

    # Perform pre-processing
    obstacles = preprocess(game_state)
    directions = ["up", "down", "left", "right"]
    danger_risk = {"up": 0.0, "down": 0.0, "left": 0.0, "right": 0.0}
    my_head = game_state['you']['head']

    # Avoid hitting the walls
    danger_risk = avoid_walls(game_state, my_head, danger_risk)

    # Avoid hitting snakes
    danger_risk = avoid_snake_bodies(obstacles, my_head, danger_risk)

    # Get lowest risk value
    min_risk = min(danger_risk.values())

    # Choose a random move from saffest moves
    safe_moves = [
        move 
        for move in danger_risk 
        if danger_risk[move] == min_risk
    ]
    random.shuffle(safe_moves)  # Shuffle to avoid bias
    if len(safe_moves) == 1:
        next_move = safe_moves[0]
        if args.print_level >= 3:
            print(f"MOVE {game_state['turn']}: Best move is {next_move}!")
    else:
        # Predict outcomes for all safe moves
        predictions = []
        for move in safe_moves:
            # Send game state and action to model
            predictions.append(predictor.predict(
                game_state, move, game_state['you']['id']
            ))

        # Select best move
        sorted_predictions = sorted(predictions, reverse=True, key=lambda x: x[1])
        next_move = sorted_predictions[0][0]
        format_predictions = [
            f"{move} ({round(prob, 3)})"
            for move, prob in sorted_predictions
        ]
        if args.print_level >= 3:
            print(f"MOVE {game_state['turn']}: Best move is {next_move}! Predictions: {format_predictions}")

    # Write state to file
    if args.save_games:
        with open(f"games/{game_state['game']['id']}.json", "a") as fp:
            json.dump(game_state, fp)
            fp.write('\n')

    # Respond to server
    return {'move': next_move}


# end is called when your Battlesnake finishes a game
def end(game_state: typing.Dict):
    print("GAME OVER\n")
    # Save game data
    if args.save_games:
        previous_actions = get_previous_actions(game_state)
        with open(f"games/{game_state['game']['id']}.json", "a") as fp:
            json.dump(previous_actions, fp)
            fp.write('\n')
            # Last snake alive is the winner
            if len(game_state['board']['snakes']) == 0:
                json.dump({'winner': ''}, fp)
            else:
                json.dump({'winner': game_state['board']['snakes'][0]['id']}, fp)
        global ongoing_games
    stats['games'] += 1
    max_len, turns_survived = ongoing_games[game_state['game']['id']][game_state['you']['id']]
    stats['sizes'].append(max_len)
    stats['turns'].append(turns_survived)
    del ongoing_games[game_state['game']['id']][game_state['you']['id']]
    if len(ongoing_games[game_state['game']['id']]) == 0:
        del ongoing_games[game_state['game']['id']]
    winners = [snake['id'] for snake in game_state['board']['snakes']]
    if len(winners) == 1:
        if game_state['you']['id'] in winners:
            stats['wins'] += 1
        else:
            stats['losses'] += 1
    else:
        stats['losses'] += 1
    # Print game stats
    print('STATS:')
    print(f"Games: {stats['games']}", f"Wins: {stats['wins']}", f"Losses: {stats['losses']}")
    print(f"Average max body size: {sum(stats['sizes'])/len(stats['sizes']):.1f}")
    print(f"Average turns survived: {sum(stats['turns'])/len(stats['turns']):.1f}")


# Start server when `python main.py` is run
if __name__ == "__main__":
    from server import run_server

    run_server({"info": info, "start": start, "move": move, "end": end}, args.port, args.deployed)
