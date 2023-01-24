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

from snakeSupervision.predictor import Predictor

parser = argparse.ArgumentParser()
parser.add_argument('-c', '--color', default=str(
    hex(random.randrange(0, 2**24))
))
parser.add_argument('-p', '--port', default='8001')
parser.add_argument('-s', '--save_games', action='store_true')
parser.add_argument('-d', '--deployed', action='store_true')
parser.add_argument('-m', '--model', default='basicModel.h5')
parser.add_argument('--stats_file', help='Path to store game stats')
args = parser.parse_args()

predictor  = Predictor(args.model)
game_stats = {
    'gametypes': {
        'solo': {
            'games_played': 0,
            'turns_survived': [],
            'longest_survival': 0,
            'turns_survived_avg': 0
        },
        'multi': {  # Dicts to save stats for individual opponents
            'games_played': {},
            'wins': {},
            'losses': {},
            'draws': {},
            'turns_survived': {},
            'longest_survival': {},
            'turns_survived_avg': {}
        }
    }
}

# info is called when you create your Battlesnake on play.battlesnake.com
# and controls your Battlesnake's appearance
# TIP: If you open your Battlesnake URL in a browser you should see this data
def info() -> typing.Dict:
    print("INFO")
    return {
        "apiversion": "1",
        "author": "me",  # TODO: Your Battlesnake Username
        "color": args.color,
        "head": "cosmic-horror",
        "tail": "mystic-moon",
    }


# start is called when your Battlesnake begins a game
def start(game_state: typing.Dict):
    print("GAME START")
    print(f"Height: {game_state['board']['height']} Width: {game_state['board']['width']}")
    # Save current opponents
    if game_state['game']['ruleset']['name'] != 'solo':
        global current_opponents
        current_opponents = [
            snake['name']
            for snake in game_state['board']['snakes']
            if snake['id'] != game_state['you']['id']
        ]
        # Add opponent to game_stats if not already there
        for snake_name in current_opponents:
            if snake_name not in game_stats['gametypes']['multi']['games_played']:
                game_stats['gametypes']['multi']['games_played'][snake_name] = 0
                game_stats['gametypes']['multi']['wins'][snake_name] = 0
                game_stats['gametypes']['multi']['losses'][snake_name] = 0
                game_stats['gametypes']['multi']['draws'][snake_name] = 0
                game_stats['gametypes']['multi']['turns_survived'][snake_name] = []
                game_stats['gametypes']['multi']['longest_survival'][snake_name] = 0
                game_stats['gametypes']['multi']['turns_survived_avg'][snake_name] = 0


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
    # Update game stats
    global game_stats
    if game_state['game']['ruleset']['name'] == 'solo':
        # Update solo game stats
        game_stats['gametypes']['solo']['games_played'] += 1
        game_stats['gametypes']['solo']['turns_survived'].append(game_state['turn'])
        game_stats['gametypes']['solo']['turns_survived_avg'] = sum(
            game_stats['gametypes']['solo']['turns_survived']
        ) / game_stats['gametypes']['solo']['games_played']

        if game_state['turn'] > game_stats['gametypes']['solo']['longest_survival']:
            game_stats['gametypes']['solo']['longest_survival'] = game_state['turn']

        print("SOLO STATS:")
        stats_string = "{:<12} | {:<7} | {:<10}\n-----------------------------------\n{:<12} | {:<7} | {:<10}".format(
            'Games Played', 'Longest', 'Avg Length',
            game_stats['gametypes']['solo']['games_played'],
            game_stats['gametypes']['solo']['longest_survival'],
            game_stats['gametypes']['solo']['turns_survived_avg']
        )
        print(stats_string)
        if args.stats_file is not None:
            with open('stats/'+args.stats_file+'_solo.stats', 'w') as f:
                f.write(stats_string)
    else:
        # Save stats for each opponent
        global current_opponents
        for snake_name in current_opponents:
            game_stats['gametypes']['multi']['games_played'][snake_name] += 1

            if len(game_state['board']['snakes']) == 0:
                game_stats['gametypes']['multi']['draws'][snake_name] += 1
            elif game_state['board']['snakes'][0]['id'] == game_state['you']['id']:
                game_stats['gametypes']['multi']['wins'][snake_name] += 1
            else:
                game_stats['gametypes']['multi']['losses'][snake_name] += 1
            
            game_stats['gametypes']['multi']['turns_survived'][snake_name].append(game_state['turn'])
            game_stats['gametypes']['multi']['turns_survived_avg'][snake_name] = sum(
                game_stats['gametypes']['multi']['turns_survived'][snake_name]
            ) / game_stats['gametypes']['multi']['games_played'][snake_name]
            if game_state['turn'] > game_stats['gametypes']['multi']['longest_survival'][snake_name]:
                game_stats['gametypes']['multi']['longest_survival'][snake_name] = game_state['turn']
            
            print("MULTIPLAYER STATS:")
            stats_string = "{:<13} | {:<12} | {:<4} | {:<6} | {:<5} | {:<7} | {:<10}\n".format(
                'Opponent Name', 'Games Played', 'Wins', 'Losses', 'Draws', 'Longest', 'Avg Length'
            )
            stats_string += "--------------------------------------------------------------------------\n"
            for snake_name in game_stats['gametypes']['multi']['games_played']:
                stats_string += "{:<13} | {:<12} | {:<4} | {:<6} | {:<5} | {:<7} | {:<10}\n".format(
                    snake_name,
                    game_stats['gametypes']['multi']['games_played'][snake_name],
                    game_stats['gametypes']['multi']['wins'][snake_name],
                    game_stats['gametypes']['multi']['losses'][snake_name],
                    game_stats['gametypes']['multi']['draws'][snake_name],
                    game_stats['gametypes']['multi']['longest_survival'][snake_name],
                    game_stats['gametypes']['multi']['turns_survived_avg'][snake_name]
                )
            print(stats_string)
            if args.stats_file is not None:
                with open(args.stats_file+'_multi.stats', 'w') as f:
                    f.write(stats_string)


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


# Given a square, return all adjacent squares that are in bounds
def get_adjacent(position: typing.Dict, game_state: typing.Dict):
    up = {'y': position['y']+1, 'x': position['x']}
    down = {'y': position['y']-1, 'x': position['x']}
    left = {'x': position['x']-1, 'y': position['y']}
    right = {'x': position['x']+1, 'y': position['y']}
    return [ 
        pos for pos in [up, down, left, right]
        if pos['y'] >= 0
        if pos['y'] <= game_state['board']['height']
        if pos['x'] >= 0
        if pos['x'] <= game_state['board']['width']
    ]


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


# Given game state & current safe moves, determines fatal out-of-bounds moves 
# returns updated safe moves
def avoid_walls(game_state: typing.Dict, danger_risk: typing.Dict)-> typing.Dict:
    my_head = game_state["you"]["body"][0]  # Coordinates of your head
    board_width = game_state['board']['width']
    board_height = game_state['board']['height']

    # Left wall is at x = -1, don't go there
    if my_head['x'] == 0:
        danger_risk['left'] += 1

    # Right wall is at x = board_width, don't go there
    elif my_head['x'] == board_width-1:
        danger_risk['right'] += 1

    # Bottom wall is at y = -1, don't go there
    if my_head['y'] == 0:
        danger_risk['down'] += 1

    # Top wall is at y = board_height, don't go there
    elif my_head['y'] == board_height-1:
        danger_risk['up'] += 1

    return danger_risk


# Given game state & current safe moves, determines moves that will be fatal colision
# with any snake body. Returns updated safe moves.
def avoid_snake_bodies(game_state: typing.Dict, danger_risk: typing.Dict)-> typing.Dict:
    my_head = game_state["you"]["body"][0]  # Coordinates of your head

    for move in danger_risk:
        next_head = get_move_position(my_head, move)
        # Loop through all snakes on the board
        for snake in game_state['board']['snakes']:
            # Loop through all body parts of this snake
            for square in snake['body'][:-1]:   # Skip the tail, handled below
                if square == next_head:
                    danger_risk[move] += 1
            # Tail is a special case, if the snake can't eat then it can't grow
            # Let the model handle this case

    return danger_risk


def avoid_neck(game_state: typing.Dict, danger_risk: typing.Dict)-> typing.Dict:
    my_head = game_state["you"]["body"][0]  # Coordinates of your head
    my_neck = game_state["you"]["body"][1]  # Coordinates of your "neck"

    if my_neck["x"] < my_head["x"]:  # Neck is left of head, don't move left
        danger_risk["left"] += 1

    elif my_neck["x"] > my_head["x"]:  # Neck is right of head, don't move right
        danger_risk["right"] += 1

    elif my_neck["y"] < my_head["y"]:  # Neck is below head, don't move down
        danger_risk["down"] += 1

    elif my_neck["y"] > my_head["y"]:  # Neck is above head, don't move up
        danger_risk["up"] += 1

    return danger_risk


# move is called on every turn and returns your next move
# Valid moves are "up", "down", "left", or "right"
# See https://docs.battlesnake.com/api/example-move for available data
def move(game_state: typing.Dict) -> typing.Dict:
    # Record actions taken by each snake in previous turn and write to file
    if game_state['turn'] > 0 and args.save_games:
        previous_actions = get_previous_actions(game_state)
        with open(f"games/{game_state['game']['id']}.json", "a") as fp:
            json.dump(previous_actions, fp)
            fp.write('\n')


    directions = ["up", "down", "left", "right"]
    danger_risk = {"up": 0.0, "down": 0.0, "left": 0.0, "right": 0.0}

    # Avoid your own neck
    danger_risk = avoid_neck(game_state, danger_risk)

    # Avoid hitting the walls
    danger_risk = avoid_walls(game_state, danger_risk)

    # Avoid hitting snakes
    danger_risk = avoid_snake_bodies(game_state, danger_risk)

    # Sort directions by danger risk
    sorted_risk = sorted(directions, key=lambda x: danger_risk[x])

    # For all moves with lowest risk, predict outcomes with model
    safe_moves = [
        move
        for move in sorted_risk
        if danger_risk[move] == danger_risk[sorted_risk[0]]
    ]
    random.shuffle(safe_moves)  # Shuffle to avoid bias
    if len(safe_moves) == 1:
        next_move = safe_moves[0]
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
        print(f"MOVE {game_state['turn']}: Best move is {next_move}! Predictions: {format_predictions}")

    # Write state to file
    if args.save_games:
        with open(f"games/{game_state['game']['id']}.json", "a") as fp:
            json.dump(game_state, fp)
            fp.write('\n')

    # Respond to server
    return {'move': next_move}

# Start server when `python main.py` is run
if __name__ == "__main__":
    from server import run_server

    run_server({"info": info, "start": start, "move": move, "end": end}, args.port, args.deployed)
