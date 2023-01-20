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
    return {
        "apiversion": "1",
        "author": "me",  # TODO: Your Battlesnake Username
        "color": sys.argv[2],  # TODO: Choose color
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


# Given a square, return all adjacent squares that are in bounds
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

    # Left wall is at x = -1, don't go there
    if my_head['x'] == 0:
        is_move_safe['left'] = False

    # Right wall is at x = board_width, don't go there
    elif my_head['x'] == board_width-1:
        is_move_safe['right'] = False

    # Bottom wall is at y = -1, don't go there
    if my_head['y'] == 0:
        is_move_safe['down'] = False

    # Top wall is at y = board_height, don't go there
    elif my_head['y'] == board_height-1:
        is_move_safe['up'] = False

    return is_move_safe


# Given game state & current safe moves, determines moves that will be fatal colision
# with any snake body. Returns updated safe moves.
def avoid_snakes(game_state: typing.Dict, is_move_safe: typing.Dict)-> typing.Dict:
    my_head = game_state["you"]["body"][0]  # Coordinates of your head

    # Loop through all snakes on the board
    for snake in game_state['board']['snakes']:

        # Loop through all body parts of this snake
        for square in snake['body']:

            # If this body part has the same x position as our head 
            # then it must be above/below us
            if square['x'] == my_head['x']:

                # If it's directly above us then don't move up
                if square['y'] == my_head['y'] + 1:
                    is_move_safe['up'] = False

                # If it's directly below us then don't move down
                elif square['y'] == my_head['y'] - 1:
                    is_move_safe['down'] = False

            # If this body part has the same y position as our head
            # then it must be to the left/right of us
            elif square['y'] == my_head['y']:

                # If it's directly to the right of us then don't move right
                if square['x'] == my_head['x'] + 1:
                    is_move_safe['right'] = False

                # If it's directly to the left of us then don't move left
                elif square['x'] == my_head['x'] - 1:
                    is_move_safe['left'] = False

    return is_move_safe


def avoid_heads(game_state: typing.Dict, is_move_safe: typing.Dict)-> typing.Dict:
    my_head = game_state["you"]["body"][0]  # Coordinates of your head

    # Loop through all snakes on the board
    for snake in game_state['board']['snakes']:

        # Don't avoid your own head
        if snake['id'] == game_state['you']['id']:
            continue    # Skip to next snake
        
        # Get the head of this snake
        other_head = snake['body'][0]

        # Get possible moves for this snake's head
        possible_moves = get_adjacent(other_head, game_state)

        # Loop through all possible moves for this snake's head
        for move in possible_moves:
            
            # If this square has the same x position as our head
            # then it must be above/below us
            if move['x'] == my_head['x']:
                
                # If it's directly above us then don't move up
                if move['y'] == my_head['y'] + 1:
                    is_move_safe['up'] = False

                # If it's directly below us then don't move down
                elif move['y'] == my_head['y'] - 1:
                    is_move_safe['down'] = False

            # If this square has the same y position as our head
            # then it must be to the left/right of us
            elif move['y'] == my_head['y']:

                # If it's directly to the right of us then don't move right
                if move['x'] == my_head['x'] + 1:
                    is_move_safe['right'] = False

                # If it's directly to the left of us then don't move left
                elif move['x'] == my_head['x'] - 1:
                    is_move_safe['left'] = False

    return is_move_safe


def avoid_neck(game_state: typing.Dict, is_move_safe: typing.Dict)-> typing.Dict:
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

    return is_move_safe


# Given list of safe moves, returns list of moves that contain food
def eat_food(game_state: typing.Dict, safe_moves: typing.Dict)-> typing.Dict:
    # Make a copy of safe moves
    moves_with_food = safe_moves.copy()

    my_head = game_state["you"]["body"][0]  # Coordinates of your head

    # If moving up is safe, check if there is food there
    if safe_moves['up'] == True:
        up_move = {'x': my_head['x'], 'y': my_head['y'] + 1}
        if up_move not in game_state['board']['food']:
            moves_with_food['up'] = False
    
    # If moving down is safe, check if there is food there
    if safe_moves['down'] == True:
        down_move = {'x': my_head['x'], 'y': my_head['y'] - 1}
        if down_move not in game_state['board']['food']:
            moves_with_food['down'] = False

    # If moving left is safe, check if there is food there
    if safe_moves['left'] == True:
        left_move = {'x': my_head['x'] - 1, 'y': my_head['y']}
        if left_move not in game_state['board']['food']:
            moves_with_food['left'] = False

    # If moving right is safe, check if there is food there
    if safe_moves['right'] == True:
        right_move = {'x': my_head['x'] + 1, 'y': my_head['y']}
        if right_move not in game_state['board']['food']:
            moves_with_food['right'] = False

    return moves_with_food


# move is called on every turn and returns your next move
# Valid moves are "up", "down", "left", or "right"
# See https://docs.battlesnake.com/api/example-move for available data
def move(game_state: typing.Dict) -> typing.Dict:

    is_move_safe = {"up": True, "down": True, "left": True, "right": True}

    # Avoid your own neck
    is_move_safe = avoid_neck(game_state, is_move_safe)

    # Avoid hitting the walls
    is_move_safe = avoid_walls(game_state, is_move_safe)

    # Avoid hitting snakes
    is_move_safe = avoid_snakes(game_state, is_move_safe)

    # Avoid hitting heads
    is_move_safe =  avoid_heads(game_state, is_move_safe)
    
    # Are there any safe moves left?
    safe_moves = []
    for move, isSafe in is_move_safe.items():
        if isSafe:
            safe_moves.append(move)

    # Check for moves that get food
    moves_with_food = eat_food(game_state, is_move_safe)

    # Are there any food moves?
    food_moves = []
    for move, hasFood in moves_with_food.items():
        if hasFood:
            food_moves.append(move)

    if len(food_moves) > 0:
        # Choose a random food move (these moves are safe)
        next_move = random.choice(food_moves)

        print(f"MOVE {game_state['turn']}: {next_move}")
        return {"move": next_move}
    elif len(safe_moves) > 0:
        # Choose a random move from the safe ones
        next_move = random.choice(safe_moves)

        print(f"MOVE {game_state['turn']}: {next_move}")
        return {"move": next_move}
    else:
        print(f"MOVE {game_state['turn']}: No safe moves detected! Moving randomly!")
        next_move = random.choice(["up", "down", "left", "right"])
        return {'move': next_move}


# Start server when `python main.py` is run
if __name__ == "__main__":
    from server import run_server

    run_server({"info": info, "start": start, "move": move, "end": end}, sys.argv[1])
