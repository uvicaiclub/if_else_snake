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
import random
import typing

parser = argparse.ArgumentParser()
parser.add_argument('-c', '--color', default=str(
    hex(random.randrange(0, 2**24))
))
parser.add_argument('-p', '--port', default='8001')
parser.add_argument('-d', '--deployed', action='store_true')
parser.add_argument('-s', '--save_games', action='store_true')
args = parser.parse_args()

games_won = 0

# info is called when you create your Battlesnake on play.battlesnake.com
# and controls your Battlesnake's appearance
# TIP: If you open your Battlesnake URL in a browser you should see this data
def info() -> typing.Dict:
    print("INFO")
    return {
        "apiversion": "1",
        "author": "me",  # TODO: Your Battlesnake Username
        "color": args.color,
        "head": "beluga",
        "tail": "round-bum",
    }


# start is called when your Battlesnake begins a game
def start(game_state: typing.Dict):
    print("GAME START")
    print(f"Height: {game_state['board']['height']} Width: {game_state['board']['width']}")


# end is called when your Battlesnake finishes a game
def end(game_state: typing.Dict):
    print("GAME OVER\n")
    global games_won
    if game_state['board']['snakes'][0]['id'] == game_state['you']['id']:
        games_won += 1
    print(f"Games won: {games_won}")


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
def get_move_position(head: typing.Dict, direction: str):
    if direction == 'up':
        return {'y': head['y']+1, 'x': head['x']}
    elif direction == 'down':
        return {'y': head['y']-1, 'x': head['x']}
    elif direction == 'left':
        return {'x': head['x']-1, 'y': head['y']}
    elif direction == 'right':
        return {'x': head['x']+1, 'y': head['y']}


# Given list of directions and head, returns all directions that will yield food
def food_moves(game_state: typing.Dict, head: typing.Dict, directions: typing.Dict)-> typing.Dict:
    directions_with_food  = []
    for move in directions:
        next_head = get_move_position(head, move)
        if next_head in game_state['board']['food']:
            directions_with_food.append(move)

    return directions_with_food


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
def avoid_snakes(game_state: typing.Dict, danger_risk: typing.Dict)-> typing.Dict:
    my_head = game_state["you"]["body"][0]  # Coordinates of your head

    for move in danger_risk:
        next_head = get_move_position(my_head, move)
        # Loop through all snakes on the board
        for snake in game_state['board']['snakes']:
            # Loop through all body parts of this snake
            for square in snake['body'][:-1]:   # Skip the tail, hadled below
                if square == next_head:
                    danger_risk[move] += 1
            # Tail is a special case, if the snake can't eat then it can't grow
            if snake['body'][-1] == next_head:
                for head_reach in get_adjacent(snake['head'], game_state):
                    if head_reach in game_state['board']['food']:
                        danger_risk[move] += 1

    return danger_risk


# Add risk of collisions with other snakes' heads
def avoid_heads(game_state: typing.Dict, danger_risk: typing.Dict)-> typing.Dict:
    my_head = game_state['you']['head']  # Position of your head

    # Loop through possible moves
    for move in danger_risk:
        next_head = get_move_position(my_head, move)
        # Loop through all snakes on the board
        for snake in game_state['board']['snakes']:
            # Don't avoid your own head
            if snake['head'] == my_head:
                continue
            # Get possible moves for this snake
            adversary_moves = get_adjacent(snake['body'][0], game_state)

            # Loop through all possible moves for this snake's head
            for adversary_move in adversary_moves:
                if  adversary_move == next_head:
                    danger_risk[move] += 0.25   # A wild guess

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

    directions = ["up", "down", "left", "right"]
    danger_risk = {"up": 0.0, "down": 0.0, "left": 0.0, "right": 0.0}

    # Avoid your own neck
    danger_risk = avoid_neck(game_state, danger_risk)

    # Avoid hitting the walls
    danger_risk = avoid_walls(game_state, danger_risk)

    # Avoid hitting snakes
    danger_risk = avoid_snakes(game_state, danger_risk)

    # Avoid hitting heads
    danger_risk =  avoid_heads(game_state, danger_risk)

    # Sort directions by danger risk
    sorted_risk = sorted(directions, key=lambda x: danger_risk[x])

    # For all moves with lowest risk, check if there is food there
    safe_moves = [
        move 
        for move in sorted_risk 
        if danger_risk[move] == danger_risk[sorted_risk[0]]
    ]
    random.shuffle(safe_moves)  # Shuffle to avoid bias
    
    nom_nom_nom = food_moves(game_state, game_state['you']['head'], safe_moves)
    if len(nom_nom_nom) > 0:
        next_move = nom_nom_nom[0]
    else:
        next_move = safe_moves[0]

    print(f"MOVE {game_state['turn']}: {next_move} | {danger_risk}")
    # Send response to server
    return {"move": next_move}


# Start server when `python main.py` is run
if __name__ == "__main__":
    from server import run_server

    run_server({"info": info, "start": start, "move": move, "end": end}, args.port, args.deployed)
