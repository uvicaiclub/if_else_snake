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

from inspect import ismemberdescriptor
from operator import is_
import random
import tarfile
import typing
import sys


# info is called when you create your Battlesnake on play.battlesnake.com
# and controls your Battlesnake's appearance
# TIP: If you open your Battlesnake URL in a browser you should see this data
def info() -> typing.Dict:
    print("INFO")
    if sys.argv[2] == 'red':
        colorCode = '#FF0000'
    elif sys.argv[2] == 'green':
        colorCode = '#00FF00'
    elif sys.argv[2] == 'blue':
        colorCode = '#0000FF'
    else:
        colorCode = "#888888"
    return {
        "apiversion": "1",
        "author": "me",  # TODO: Your Battlesnake Username
        "color": colorCode,  # TODO: Choose color
        "head": "default",  # TODO: Choose head
        "tail": "default",  # TODO: Choose tail
    }


# start is called when your Battlesnake begins a game
def start(game_state: typing.Dict):
    print("GAME START")
    print(f"Height: {game_state['board']['height']} Width: {game_state['board']['width']}")


# end is called when your Battlesnake finishes a game
def end(game_state: typing.Dict):
    print("GAME OVER\n")


def get_adjacent(square: typing.Dict, game_state: typing.Dict):
    up = {'y': square['y']+1, 'x': square['x']}
    down = {'y': square['y']-1, 'x': square['x']}
    left = {'x': square['x']-1, 'y': square['y']}
    right = {'x': square['x']+1, 'y': square['y']}
    return [ 
        pos for pos in [up, down, left, right]
        if pos['y'] >= 0
        if pos['y'] <= game_state['board']['height']
        if pos['x'] >= 0
        if pos['x'] <= game_state['board']['width']
    ]


# Given game state & current safe moves, determines fatal out-of-bounds moves 
# returns updated safe moves
def avoid_walls(game_state: typing.Dict, is_move_safe: typing.Dict)-> typing.Dict:
    my_head = game_state["you"]["body"][0]  # Coordinates of your head
    board_width = game_state['board']['width']
    board_height = game_state['board']['height']
    if my_head['x'] == 0:
        is_move_safe['left'] = False
    elif my_head['x'] == board_width-1:
        is_move_safe['right'] = False
    if my_head['y'] == 0:
        is_move_safe['down'] = False
    elif my_head['y'] == board_height-1:
        is_move_safe['up'] = False
    return is_move_safe


# Given game state & current safe moves, determines moves that will be fatal colision
# with any snake body. Also determines moves that enter the space of a snakes tail.
# returns updated safe moves & possible tail colision moves
def avoid_torsos(game_state: typing.Dict, is_move_safe: typing.Dict)-> typing.Tuple[typing.Dict, typing.Dict]:
    my_head = game_state["you"]["body"][0]  # Coordinates of your head
    torso_parts = [ 
        part 
        for snake in game_state['board']['snakes'] 
        for part in snake['body']
    ]
    tails = [
        snake['body'][-1]
        for snake in game_state['board']['snakes']
    ]
    for part in torso_parts:
        if my_head['y'] == part['y']:
            if my_head['x']-1 == part['x']:
                is_move_safe['left'] = False
            elif my_head['x']+1 == part['x']:
                is_move_safe['right'] = False
        elif my_head['x'] == part['x']:
            if my_head['y']-1 == part['y']:
                is_move_safe['down'] = False
            elif my_head['y']+1 == part['y']:
                is_move_safe['up'] = False
    possible_tails = is_move_safe.copy()
    for tail in tails:
        if my_head['y'] == tail['y']:
            if my_head['x']-1 == tail['x']:
                possible_tails['left'] = True
            elif my_head['x']+1 == tail['x']:
                possible_tails['right'] = True
        elif my_head['x'] == tail['x']:
            if my_head['y']-1 == tail['y']:
                possible_tails['down'] = True
            elif my_head['y']+1 == tail['y']:
                possible_tails['up'] = True
    return is_move_safe, possible_tails


def avoid_heads(game_state: typing.Dict, is_move_safe: typing.Dict)-> typing.Tuple[typing.Dict, typing.Dict, typing.Dict]:
    my_head = game_state["you"]["body"][0]  # Coordinates of your head
    my_len = len(game_state["you"]["body"])
    other_heads = [
        (snake['body'][0], len(snake['body']))
        for snake in game_state['board']['snakes']
        if snake['id'] != game_state["you"]['id']
    ]
    torso_parts = [ 
        part 
        for snake in game_state['board']['snakes'] 
        for part in snake['body']
    ]
    possible_heads = is_move_safe.copy()
    kill_moves = is_move_safe.copy()
    for head, snake_len in other_heads:
        # Get spaces adjacent to other head
        possible_moves = get_adjacent(head, game_state)
        # Mark moves that enter these adjacent spaces based on snake lengths
        # TODO: better kills moves handling
        for space in possible_moves:
            if my_head['y'] == space['y']:
                if my_head['x']-1 == space['x']:
                    if snake_len >= my_len:
                        is_move_safe['left'] = False
                    elif is_move_safe['left']:
                        kill_moves['left'] = True
                elif my_head['x']+1 == space['x']:
                    if snake_len >= my_len:
                        is_move_safe['right'] = False
                    elif is_move_safe['right']:
                        kill_moves['right'] = True
            elif my_head['x'] == space['x']:
                if my_head['y']-1 == space['y']:
                    if snake_len >= my_len:
                        is_move_safe['down'] = False
                    elif is_move_safe['down']:
                        kill_moves['down'] = True
                elif my_head['y']+1 == space['y']:
                    if snake_len >= my_len:
                        is_move_safe['up'] = False
                    elif is_move_safe['up']:
                        kill_moves['up'] = True
    return is_move_safe, possible_heads, kill_moves


# move is called on every turn and returns your next move
# Valid moves are "up", "down", "left", or "right"
# See https://docs.battlesnake.com/api/example-move for available data
def move(game_state: typing.Dict) -> typing.Dict:

    is_move_safe = {"up": True, "down": True, "left": True, "right": True}

    # We've included code to prevent your Battlesnake from moving backwards
    my_head = game_state["you"]["body"][0]  # Coordinates of your head
    my_neck = game_state["you"]["body"][1]  # Coordinates of your "neck"

    if my_neck["x"] < my_head["x"]:  # Neck is left of head, don't move left
        is_move_safe["left"] = False

    elif my_neck["x"] > my_head["x"]:  # Neck is right of head, don't move right
        is_move_safe["right"] = False

    elif my_neck["y"] < my_head["y"]:  # Neck is below head, don't move down
        is_move_safe["down"] = False

    elif my_neck["y"] > my_head["y"]:  # Neck is above head, don't move up
        is_move_safe["up"] = False

    # Remove fatal out-of-bounds moves
    is_move_safe = avoid_walls(game_state, is_move_safe)

    # Remove fatal torso colisions
    is_move_safe, possible_tails = avoid_torsos(game_state, is_move_safe)
    # TODO: possible_tails does not contain head risks, need better way to manage risk moves
    # Remove possible head colision
    is_move_safe, possible_heads, kill_moves =  avoid_heads(game_state, is_move_safe)

    # Are there any kill moves?
    kill_moves = []
    for move, isKill in kill_moves:
        if isKill:
            kill_moves.append(move)
    
    # Are there any safe moves left?
    safe_moves = []
    for move, isSafe in is_move_safe.items():
        if isSafe:
            safe_moves.append(move)

    # Are there any tail-collision risk moves left?
    tail_risk_moves = []
    for move, isTailRisk in possible_tails.items():
        if isTailRisk:
            tail_risk_moves.append(move)

    # Are there any head-collision risk moves left?
    head_risk_moves = []
    for move, isHeadRisk in possible_heads.items():
        if isHeadRisk:
            head_risk_moves.append(move)


    if len(kill_moves) > 0:
        next_move = random.choice(kill_moves)
        print(f"MOVE (kill) {game_state['turn']}: {next_move}")
        return {"move": next_move}
    elif len(safe_moves) > 0:
        # Choose a random move from the safe ones
        next_move = random.choice(safe_moves)

        # TODO: Step 4 - Move towards food instead of random, to regain health and survive longer
        # food = game_state['board']['food']

        print(f"MOVE {game_state['turn']}: {next_move}")
        return {"move": next_move}
    elif len(tail_risk_moves) > 0:
        next_move = random.choice(tail_risk_moves)
        print(f"MOVE (tails) {game_state['turn']}: {next_move}")
        return {"move": next_move}
    elif len(head_risk_moves) > 0:
        next_move = random.choice(head_risk_moves)
        print(f"MOVE (heads) {game_state['turn']}: {next_move}")
        return {"move": next_move}
    else:
        print(f"MOVE {game_state['turn']}: No safe moves detected! Moving randomly!")
        next_move = random.choice(["up", "down", "left", "right"])
        return {'move': next_move}


# Start server when `python main.py` is run
if __name__ == "__main__":
    from server import run_server

    run_server({"info": info, "start": start, "move": move, "end": end}, sys.argv[1])
