from collections import defaultdict
import multiprocessing as mp
from itertools import product
from enigma import enigma, bombe, utils

def run_bombe(bomba: bombe.Bombe, menu: dict, q: mp.Queue):
    possibilities = bomba.run(menu, menu['paths'])
    # Need to organise possibilities such that they can be 
    # checked
    if len(possibilities) > 0:
        for plugboard, rotor_offset_possibilities in possibilities.items():
            # Configure the machine and score the ciphertext
            for rotor_offsets in rotor_offset_possibilities:
                machine.rotors[0].configure(
                    ring_setting[0], rotor_offsets[0]
                )
                machine.rotors[1].configure(
                    ring_setting[1], rotor_offsets[1]
                )
                machine.rotors[2].configure(
                    ring_setting[2], rotor_offsets[2]
                )
                machine.configure(
                    machine.rotors, machine.reflector, plugboard
                )
                for _ in range(menu['offset']):
                    machine.unstep()
                scores.append([(
                    machine.copy(),
                    utils.score_text(
                        machine.encrypt(ciphertext)
                    )
                )])
    q.put(scores)    

with open('ciphertext.txt') as infile:
    ciphertext = infile.read().replace(' ', '')

with open('cribs.txt') as infile:
    cribs = [c.replace(' ', '').upper() for c in infile.read().split('\n')]

# Find possible positions, menus, and menu paths for each crib
menus = []
for crib in cribs:
    for pos in utils.find_crib_positions(crib, ciphertext):
        menu = utils.create_menu(crib, ciphertext, pos)
        menu['offset'] = pos
        menu['paths'] = utils.find_paths_dfs(menu)
        menus.append(menu)

# The more loops the better
menus.sort(key=lambda m: -len(m['paths']))
menu = menus[0]

possible_configurations = {}
scores = []
all_ring_settings = [''.join(p) for p in product(enigma.ALPHABET, repeat=3)]
rotor_a: enigma.Rotor
rotor_b: enigma.Rotor
rotor_c: enigma.Rotor
reflector: enigma.Reflector
# For each machine configuration, find the possible plugboard settings and 
# offsets
processes = []
queue = mp.Queue()
for reflector in enigma.REFLECTORS.values():
    for rotor_a in enigma.ROTORS.values():
        for rotor_b in enigma.ROTORS.values():
            if rotor_a == rotor_b:
                continue
            for rotor_c in enigma.ROTORS.values():
                if (
                    rotor_b == rotor_c or
                    rotor_a == rotor_c
                ):
                    continue
                for ring_setting in all_ring_settings:
                    machine = enigma.EnigmaMachine()
                    machine.configure(
                        [rotor_a.copy(), rotor_b.copy(), rotor_c.copy()],
                        reflector.copy(), ()
                    )
                    bomba = bombe.Bombe(machine, ring_setting)
                    processes.append(mp.Process(
                        target=run_bombe, args=(bomba, menu, queue)
                    ))
for p in processes:
    p.start()
for p in processes:
    p.join()

while not queue.empty():
    scores += queue.get()

best_machine: enigma.EnigmaMachine = max(scores, key=lambda t: -t[1])[0]
with open('out.txt', 'w') as outfile:
    outfile.write(
        best_machine.encrypt(ciphertext)
    )
