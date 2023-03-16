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
default=str(hex(random.randrange(0, 2**24))), help='Hex color code. Default random.')
parser.add_argument('-p', '--port', default='8001',
help='Port to run Battlesnake on. Default 8001.')
parser.add_argument('-d', '--deployed', action='store_true',
help='Opens server to the internet')
parser.add_argument('-s', '--save_games', action='store_true',
help='Save game data to file for training')
parser.add_argument('-m', '--model', default='convModel.h5',
help='Filename of model to use for predictions. Default convModel.h5')
parser.add_argument('--stats_file', help='Path to store game stats')
parser.add_argument('--print_level', default=2, choices=[1,2,3],
    help='''1: silence all prints
            2: (Default) silence move(), info(), start()
            3: print from all endpoints'''
)
args = parser.parse_args()

from snakeSupervision.predictor import Predictor

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
    return {
        "apiversion": "1",
        "author": "me",  # TODO: Your Battlesnake Username
        "color": args.color,
        "head": "cosmic-horror",
        "tail": "mystic-moon",
    }


# start is called when your Battlesnake begins a game
def start(game_state: typing.Dict):
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
    if from_pos == to_pos:
        raise Exception('from_pos and to_pos are the same')
    if to_pos['y'] > from_pos['y']:
        return 'up'
    elif to_pos['y'] < from_pos['y']:
        return 'down'
    elif to_pos['x'] > from_pos['x']:
        return 'right'
    else:
        return 'left'


# Given head position and direction, return the new head position
def get_move_position(head: typing.Dict, direction: str)-> typing.Dict:
    if direction not in ['up', 'down', 'left', 'right']:
        raise Exception('Invalid direction')
    if direction == 'up':
        return {'y': head['y']+1, 'x': head['x']}
    elif direction == 'down':
        return {'y': head['y']-1, 'x': head['x']}
    elif direction == 'left':
        return {'x': head['x']-1, 'y': head['y']}
    else:
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

    # For all moves with lowest risk, predict outcomes with model
    safe_moves = [
        move
        for move in danger_risk
        if danger_risk[move] == min(danger_risk.values())
    ]
    random.shuffle(safe_moves)  # Shuffle to avoid bias
    if game_state['turn'] == 0 or len(safe_moves) == 1:
        next_move = safe_moves[0]
        if args.print_level >= 3:
            print(f"MOVE {game_state['turn']}: Best move is {next_move}!")
    else:
        # Predict outcomes for all safe moves
        predictions = []
        for move in safe_moves:
            try:
                # Send game state and action to model
                predictions.append(predictor.predict(
                    game_state, move, game_state['you']['id']
                ))
            except ValueError:
                # If model fails to predict, set to zero
                predictions.append((move, 0.0))

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
    # Update game stats
    global game_stats
    if game_state['game']['ruleset']['name'] == 'solo':
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
            stats_string = "{:<13} | {:<12} | {:<8} | {:<4} | {:<6} | {:<5} | {:<7} | {:<10}\n".format(
                'Opponent Name', 'Games Played', 'Win/Loss', 'Wins', 'Losses', 'Draws', 'Longest', 'Avg Length'
            )
            stats_string += "--------------------------------------------------------------------------\n"
            for snake_name in game_stats['gametypes']['multi']['games_played']:
                wins = game_stats['gametypes']['multi']['wins'][snake_name]
                losses = game_stats['gametypes']['multi']['losses'][snake_name]
                if wins + losses == 0:
                    win_loss = 0
                else:
                    win_loss = round(wins / (wins + losses) * 100, 3)
                stats_string += "{:<13} | {:<12} | {:<8} | {:<4} | {:<6} | {:<5} | {:<7} | {:<10}\n".format(
                    snake_name,
                    game_stats['gametypes']['multi']['games_played'][snake_name],
                    win_loss,
                    wins,
                    losses,
                    game_stats['gametypes']['multi']['draws'][snake_name],
                    game_stats['gametypes']['multi']['longest_survival'][snake_name],
                    game_stats['gametypes']['multi']['turns_survived_avg'][snake_name]
                )
            print(stats_string)
            if args.stats_file is not None:
                with open('stats/'+args.stats_file+'_multi.stats', 'w') as f:
                    f.write(stats_string)


# Start server when `python main.py` is run
if __name__ == "__main__":
    from server import run_server

    run_server({"info": info, "start": start, "move": move, "end": end}, args.port, args.deployed)
