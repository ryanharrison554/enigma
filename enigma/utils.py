"""Module to search and handle cribs, menus, and searching
"""
from collections import defaultdict


def is_crib_position(crib: str, ciphertext: str, position: int) -> bool:
    """Validates if a given position in the ciphertext is a valid position for the given crib

    Args:
        crib (str): Crib to search for
        ciphertext (str): Ciphertext to analyse
        position (int): Position of the start of the crib in the ciphertext

    Returns:
        bool: True if the position is a valid position for the given crib
    """
    if position + len(crib) > len(ciphertext):
        return False
    
    for a, b in zip(crib, ciphertext[position:position+len(crib)]):
        if a == b:
            return False
    
    return True


def find_crib_positions(crib: str, ciphertext: str) -> list:
    """Search the ciphertext for valid positions for the given crib

    Args:
        crib (str): Crib to search for
        ciphertext (str): Ciphertext to search

    Returns:
        list[int]: List of valid positions in the ciphertext for the given crib
    """
    crib_positions = []
    for position in range(len(ciphertext) - len(crib)):
        if is_crib_position(crib, ciphertext, position):
            crib_positions.append(position)
    return crib_positions


def create_menu(crib: str, ciphertext: str, position: int) -> dict:
    """Create a bi-directional representing the menu for a given valid crib 
    position

    Args:
        crib (str): Crib in ciphertext
        ciphertext (str): Full ciphertext
        position (int): Crib position in ciphertext

    Returns:
        dict: Dictionary-based graph representing menu
    """
    menu = defaultdict(dict)
    # Each tuple is a pair of letters that are encrypted to each other plus 
    # their position in relation to the start of the crib
    triplets = zip(
        crib, ciphertext[position:position+len(crib)], range(len(crib))
    )
    for a, b, pos in triplets:
        menu[a][b] = menu[a].get(b, []) + [pos]
        menu[b][a] = menu[b].get(a, []) + [pos]
    # Include starting point in menu
    menu['input'] = crib[0]
    return menu


def find_paths_dfs(
    menu: dict,
    current_path: str=''
) -> list:
    if current_path == '':
        current_path = menu['input']
    paths = []
    path_node_sets = []
    current_node = current_path[-1]
    for connection in menu[current_node]:
        # Ensure we don't count a single connection as a loop
        if len(current_path) >= 2:
            back_connection = connection == current_path
        else:
            back_connection = False

        if connection in current_path and not back_connection:
            path = current_path + connection
            if set(path) not in path_node_sets:
                path_node_sets.append(set(path))
                paths.append(path)
        # Faster comparison than checking presence in array again
        elif not back_connection:
            path = current_path + connection
            for new_path in find_paths_dfs(menu, path):
                if set(new_path) not in path_node_sets:
                    path_node_sets.append(set(new_path))
                    paths.append(new_path)
    # If we didn't find any new paths, then we are at the edge of the graph
    # if paths == []:
    #     paths = [current_path,]
    return paths


def find_cycles(menu: dict, start: str, next: str, path=[]) -> list:
        if start == next and next in path:
            return [path]
        if not menu.get(next, False):
            return []
        path = path + [next]
        paths = []
        for node in menu[start]:
            if node not in path:
                newpaths = find_cycles(menu, node, next, path)
                paths += newpaths
        return paths


def get_menu_cycles(menu: dict) -> list:
    """Depth-first search for cycles in a menu
    
    Args:
        menu (dict): Menu graph represented by a dict

    Returns:
        list: Cycles found in the menu
    """
    # Find cycles for all letters
    cycles = []
    for starting_letter in menu.keys():
        cycles += find_cycles(menu, starting_letter, starting_letter)
    
    # Find truly unique cycles
    unique_cycles = []
    cycle_sets = []
    for cycle in cycles:
        cycle_as_set = set(cycle)
        if cycle_as_set not in unique_cycles:
            unique_cycles.append(cycle)
            cycle_sets.append(cycle_as_set)
        
    return unique_cycles


def score_text(plaintext: str) -> int:
    """Return a score ranking texts based on character frequencies in the 
    English language
    """
    english_frequencies = {
        'A': .08167,
        'B': .01492,
        'C': .02202,
        'D': .04253,
        'E': .12702,
        'F': .02228,
        'G': .02015,
        'H': .06094,
        'I': .06996,
        'J': .00153,
        'K': .01292,
        'L': .04025,
        'M': .02406,
        'N': .06749,
        'O': .07507,
        'P': .01929,
        'Q': .00095,
        'R': .05987,
        'S': .06327,
        'T': .09356,
        'U': .02758,
        'V': .00978,
        'W': .02560,
        'X': .00150,
        'Y': .01994,
        'Z': .00077,
        ' ': .13000
    }
    score = 0.0
    for char in plaintext:
        score += english_frequencies[char]
    return score