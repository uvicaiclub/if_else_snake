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
import json

parser = argparse.ArgumentParser()
parser.add_argument('-c', '--color',
default=random.choice(["#DFFF00","#FFBF00","#FF7F50","#DE3163","#9FE2BF","#40E0D0","#6495ED","#CCCCFF"]),
help='Hex color code. Default random.')
parser.add_argument('-p', '--port', default='8001',
                    help='Port to run Battlesnake on. Default 8001.')
parser.add_argument('-d', '--deployed', action='store_true',
                    help='Opens server to the internet')
parser.add_argument('--print_level', default=2, type=int, choices=[1, 2, 3],
                    help='''1: silence all prints
            2: (Default) silence move(), info(), start()
            3: print from all endpoints'''
                    )
args = parser.parse_args()

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
    if args.port != '8001':
        args.color = "#0000FF"
    return {
        "apiversion": "1",
        "author": "me",  # TODO: Your Battlesnake Username
        "color": args.color,
        "head": "beluga",
        "tail": "round-bum",
    }


# start is called when your Battlesnake begins a game
def start(game_state: typing.Dict):
    print(f"Starting {game_state['game']['ruleset']['name']}")
    # Save current opponents
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
    # Create food array
    food = [
        [0] * game_state['board']['height']
        for x in range(game_state['board']['width'])
    ]
    for food_pos in game_state['board']['food']:
        food[food_pos['x']][food_pos['y']] = 1
    return obstacles, food


# Get manhattan distance between two points
def man_dist(from_pos: typing.Dict, to_pos: typing.Dict):
    return abs(to_pos['x'] - from_pos['x']) + abs(to_pos['y'] - from_pos['y'])


# Perform A star search from start_pos to end_pos, return path
def a_star(game_state: typing.Dict, obstacles: list, food: list, start_pos: typing.Dict, end_pos: typing.Dict):
    # Frontier stores path, number of food in path, and manhattan distance to end
    frontier = []
    explored = [
        [-1] * game_state['board']['height']
        for x in range(game_state['board']['width'])
    ]
    if food[start_pos['x']][start_pos['y']] == 1:
        frontier.append(([start_pos], 1, man_dist(start_pos, end_pos)))
    else:
        frontier.append(([start_pos], 0, man_dist(start_pos, end_pos)))
    while len(frontier) > 0:
        # Get next position to explore
        path, food_count, h = frontier.pop(0)
        cur_pos = path[-1]
        # If we've reached the end, return path
        if cur_pos == end_pos:
            return path
        # If we haven't explored this position or we've explored it with a longer path, explore it
        if explored[cur_pos['x']][cur_pos['y']] == -1 or explored[cur_pos['x']][cur_pos['y']] > len(path):
            explored[cur_pos['x']][cur_pos['y']] = len(path)
            adjacent = get_adjacent_safe(game_state, obstacles, cur_pos, len(path)+1, food_count)
            for next_pos in adjacent:
                new_path = path.copy()
                new_path.append(next_pos)
                if food[next_pos['x']][next_pos['y']] == 1:
                    frontier.append((new_path, food_count+1, man_dist(next_pos, end_pos)))
                else:
                    frontier.append((new_path, food_count, man_dist(next_pos, end_pos)))
        # Sort frontier by manhattan distance + path length
        frontier.sort(key=lambda x: x[2] + len(x[0]))
    return None


# Given a position, return shortest distance to food
def get_food_dist(game_state: typing.Dict, obstacles: list, food: list, position: typing.Dict):
    shortest_dist = game_state['board']['width'] * game_state['board']['height'] + 1
    for food_pos in game_state['board']['food']:
        # Man distance is a lower bound on the actual distance
        if man_dist(position, food_pos) > shortest_dist:
            continue
        path = a_star(game_state, obstacles, food, position, food_pos)
        if path is not None:
            if len(path) < shortest_dist:
                shortest_dist = len(path)
    return shortest_dist


# Given a position, return all adjacent positions that are in bounds
def get_adjacent(game_state: typing.Dict, position: typing.Dict):
    up = {'x': position['x'], 'y': position['y']+1}
    down = {'x': position['x'], 'y': position['y']-1}
    left = {'x': position['x']-1, 'y': position['y']}
    right = {'x': position['x']+1, 'y': position['y']}
    return [
        pos for pos in [up, down, left, right]
        if pos['y'] >= 0
        if pos['y'] < game_state['board']['height']
        if pos['x'] >= 0
        if pos['x'] < game_state['board']['width']
    ]


# Given a position and time to reach it, return all adjacent positions that are
# in bounds and have obstacles with lifespans less than time_to_reach. Account for
# food count with self-collisions
def get_adjacent_safe(game_state: typing.Dict, obstacles: list, position: typing.Dict, time_to_reach: int, food_count: int):
    adjacent_positions = get_adjacent(game_state, position)
    safe = []
    for pos in adjacent_positions:
        # Check for self collision
        if pos in game_state['you']['body']:
            if time_to_reach > obstacles[pos['x']][pos['y']] + food_count:
                safe.append(pos)
        elif time_to_reach > obstacles[pos['x']][pos['y']]:
            safe.append(pos)
    return safe


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


def avoid_heads(game_state: typing.Dict, danger_risk: typing.Dict) -> typing.Dict:
    my_head = game_state['you']['head']
    my_length = len(game_state['you']['body'])
    for snake in game_state['board']['snakes']:
        head = snake['body'][0]
        next_positions = get_adjacent(game_state, head)
        for move in danger_risk:
            move_pos = get_move_position(my_head, move)
            if move_pos in next_positions:
                if len(snake['body']) >= my_length:
                    danger_risk[move] += 0.25
    return danger_risk


# Given a list of positions, return their expected volumes
def flood_fill_dfs(game_state: typing.Dict, obstacles: list, food: list, fill_from: typing.List) -> "list[typing.Dict]":
    volumes = []
    # Run DFS until path of max_depth found
    for pos in fill_from:
        # Stack to track head pos, current path, and food in path
        if food[pos['x']][pos['y']] == 1:
            frontier = [(pos, [pos], 1)]
        else:
            frontier = [(pos, [pos], 0)]
        volume = 0  # Track size of space
        # Track longest path to a position
        visited = [
            [0] * game_state['board']['height']
            for x in range(game_state['board']['width'])
        ]
        while volume <= len(game_state['you']['body']):
            if len(frontier) == 0:
                break
            # Explore next position
            next_pos, cur_path, food_in_path = frontier.pop(-1)
            path_len = len(cur_path)
            if path_len > volume:
                volume = path_len
            to_expand = get_adjacent_safe(game_state, obstacles, next_pos, path_len+1, food_in_path)
            for node in to_expand:
                # Check if this path intersects itself
                if node in cur_path:
                    # Check if this path intersects itself too soon
                    if (path_len - cur_path.index(node)) < (len(game_state['you']['body']) + 1):
                        continue
                # Check if this is longest path found to this point
                if path_len + 1 > visited[node['x']][node['y']]:
                    # Mark visited with current path length (including new node)
                    visited[node['x']][node['y']] = path_len + 1
                    # Expand if this path is longer than obstacle's lifetime
                    new_path = cur_path.copy()
                    new_path.append(node)
                    if food[node['x']][node['y']] == 1:
                        frontier.append([node, new_path, food_in_path+1])
                    else:
                        frontier.append([node, new_path, food_in_path])
        volumes.append(volume)
    return list(zip(fill_from, volumes))


# move is called on every turn and returns your next move
# Valid moves are "up", "down", "left", or "right"
# See https://docs.battlesnake.com/api/example-move for available data
def move(game_state: typing.Dict) -> typing.Dict:
    global ongoing_games
    ongoing_games[game_state['game']['id']][game_state['you']['id']] = [
        len(game_state['you']['body']),
        game_state['turn']
    ]

    # Perform pre-processing
    obstacles, food = preprocess(game_state)

    directions = ["up", "down", "left", "right"]
    danger_risk = {"up": 0.0, "down": 0.0, "left": 0.0, "right": 0.0}
    my_head = game_state['you']['head']

    # Avoid hitting the walls
    danger_risk = avoid_walls(game_state, my_head, danger_risk)

    # Avoid hitting snakes
    danger_risk = avoid_snake_bodies(obstacles, my_head, danger_risk)

    # Add head colision risk
    danger_risk = avoid_heads(game_state, danger_risk)

    # Select all moves with lowest risk
    lowest_risk = min([danger_risk[move] for move in danger_risk])
    safe_moves = [
        move
        for move in danger_risk
        if danger_risk[move] == lowest_risk
    ]
    # If more than one safe moves, measure their volumes
    if len(safe_moves) > 1:
        # Measure volumes connected to each hypothetical move
        move_positions = [
            get_move_position(game_state['you']['head'], move)
            for move in safe_moves
        ]
        volumes = flood_fill_dfs(game_state, obstacles, food, move_positions)
        # Select volumes that are at least as big as our body
        suitable_volumes = [
            volume
            for volume in volumes
            if volume[1] >= len(game_state['you']['body'])
        ]
        # Measure length of largest snake
        if len(game_state['board']['snakes']) > 1:
            biggest_snake = max([
                len(snake['body'])
                for snake in game_state['board']['snakes']
                if snake['id'] != game_state['you']['id']
            ])
        else:
            biggest_snake = 0
        if len(suitable_volumes) > 0:
            if game_state['you']['health'] < 20 or len(game_state['you']['body']) <= biggest_snake:
                # Prioritize eating if we are not the biggest snake
                min_dist = game_state['board']['width'] * game_state['board']['height'] + 1
                chosen_volume = suitable_volumes[0]
                for volume in suitable_volumes:
                    dist_to_food = get_food_dist(game_state, obstacles, food, volume[0])
                    if dist_to_food < min_dist:
                        min_dist = dist_to_food
                        chosen_volume = volume
                # Select move with shortest path to food
                next_move = safe_moves[move_positions.index(chosen_volume[0])]
            else:
                # Otherwise chose random suitable volume
                chosen_volume = random.choices(
                    suitable_volumes, 
                    weights=[volume[1] for volume in suitable_volumes]
                )[0]
                next_move = safe_moves[move_positions.index(chosen_volume[0])]
        else:
            # No suitable volumes, select random safe move and pray
            next_move = random.choice(safe_moves)
    elif len(safe_moves) == 1:
        # Only one safe move, select it
        next_move = safe_moves[0]
    else:
        # Move randomly and pray
        next_move = random.choice(directions)
    if args.print_level >= 3:
        print(f"MOVE {game_state['turn']}: {next_move} | {danger_risk}")
    # Send response to server
    return {"move": next_move}


# end is called when your Battlesnake finishes a game
def end(game_state: typing.Dict):
    print("GAME OVER\n")
    global ongoing_games
    stats['games'] += 1
    max_len, turns_survived = ongoing_games[game_state['game']['id']][game_state['you']['id']]
    stats['sizes'].append(max_len)
    stats['turns'].append(turns_survived)
    # Remove game from ongoing games
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

    run_server({"info": info, "start": start, "move": move,
               "end": end}, args.port, args.deployed)
