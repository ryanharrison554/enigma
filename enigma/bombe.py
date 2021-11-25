from collections import defaultdict
from itertools import product

from .enigma import EnigmaMachine, ALPHABET

class Bombe:
    """A single bombe machine, cycling through plugboard settings to try and 
    find contradictions
    """

    def __init__(self, machine: EnigmaMachine, ring_settings: str):
        """Initialise the bombe with a given EnigmaMachine
        
        The rotors in this enigma machine will be configured later, along with 
        the plugboard.
        
        Args:
            machine (EnigmaMachine): Enigma machine to use in the bombe
            ring_settings (str): Letters representing the ring settings for
                each rotor (right-to-left)
        """
        self.machine = machine
        self.ring_settings = ring_settings

    def add_contradiction(self, letter, letter_cipher):
        if letter not in self.contradictions:
            self.contradictions[letter] = set([letter_cipher])
        else: 
            plug_contradictions = self.contradictions[letter]
            plug_contradictions.add(letter_cipher)
            self.contradictions[letter] = plug_contradictions

        if letter_cipher not in self.contradictions:
            self.contradictions[letter_cipher] = set([letter])
        else: 
            plug_contradictions = self.contradictions[letter_cipher]
            plug_contradictions.add(letter)
            self.contradictions[letter_cipher] = plug_contradictions
    
    def run(self, menu: dict, menu_paths: list) -> list:
        """Run the bombe on a given set of paths
        
        The paths through the menu are the unique cycles in the menu we can use 
        to determine plugboard settings.
        
        For each path, we loop through letters and plugboard guesses and 
        discard any guesses that form contradictions in the cycle.
        
        Args:
            menu (dict): Dictionary graph representing the menu
            menu_paths (list): List of unique cycles in the menu
        
        Returns:
            list: List of lists of plugboard pairs that are valid possibilities 
                for the ciphertext
        """
        # Generate all possible offsets for 3 rotors
        rotor_offset_combinations = [
            ''.join(prod) for prod in product(ALPHABET, repeat=3)
        ]

        # Maps plugboard settings to rotor settings
        possibilities = defaultdict(list)

        for rotor_offsets in rotor_offset_combinations:
            # Reconfigure each rotor
            print(f'Guessing {rotor_offsets}')
            for r, rotor in enumerate(self.machine.rotors):
                rotor.configure(self.ring_settings[r], rotor_offsets[r])
        
            self.contradictions = defaultdict()

            # Start guessing plugboard settings
            for guess in ALPHABET:
                plugboard = defaultdict()
                plugboard[menu['input']] = guess
                plugboard[guess] = menu['input']
                plugboard_possible = True

                # Explore paths to check for contradictions
                for path in menu_paths:
                    for i in range(len(path) - 1):
                        # Current letter in path
                        letter = path[i]
                        # Connections to the current letter
                        letter_connections = menu[letter]

                        # Ciphertext for current letter
                        letter_cipher = path[i+1]

                        # Relative positions of letter from start of crib
                        letter_cipher_positions = letter_connections[
                            letter_cipher
                        ] 

                        # Check only first connection position for now
                        cipher_offset = letter_cipher_positions[0]

                        # Reset and step to cipher_offset
                        self.machine.reset()
                        for _ in range(cipher_offset):
                            self.machine.step()
                        
                        if letter in plugboard and plugboard_possible:
                            # Encrypt a single letter
                            plug_letter = plugboard[letter]
                            plug_letter_cipher = self.machine.encrypt(
                                plug_letter
                            )

                            # The encrypted letter has already been found in 
                            # contradictions, need to add the rest of the 
                            # contradictions
                            if letter_cipher in self.contradictions:
                                plug_contradictions = self.contradictions[
                                    letter_cipher
                                ]
                                if plug_letter_cipher in plug_contradictions:
                                    for plug in plugboard:
                                        plug_cipher = plugboard[plug]
                                        self.add_contradiction(
                                            plug, plug_cipher
                                        )
                                    # Contradiction found, time to quit checking
                                    plugboard_possible = False
                                    break
                            
                            # Letter is already in plugboard...
                            if letter_cipher in plugboard:
                                if (
                                    plugboard[letter_cipher] == 
                                    plug_letter_cipher
                                ):
                                    # Found the end of the loop, success!
                                    break
                                else:
                                    # Contradiction
                                    self.add_contradiction(
                                        letter_cipher, plug_letter_cipher
                                    )
                                    for plug in plugboard:
                                        plug_cipher = plugboard[plug]
                                        self.add_contradiction(
                                            plug, plug_cipher
                                        )
                                    plugboard_possible = False
                                    break
                            
                            # Just found a new plugboard setting
                            else:
                                plugboard[letter_cipher] = plug_letter_cipher
                                plugboard[plug_letter_cipher] = letter_cipher
                            
                    # Forget the rest of the paths, we already know it's not 
                    # possible
                    if not plugboard_possible:
                        break
                
                if plugboard_possible:
                    plugboard_pairs = []
                    for pair in plugboard.items():
                        if set(pair) not in plugboard_pairs and not len(set(pair)) == 1:
                            plugboard_pairs.append(set(pair))
                    plugboard_as_tuple = tuple(
                        [tuple(pair) for pair in plugboard_pairs]
                    )
                    possibilities[plugboard_as_tuple].append(rotor_offsets)
        
        return possibilities

                        