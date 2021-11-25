#!/usr/bin/env python
# -*- coding: utf-8 -*-

ALPHABET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
N = len(ALPHABET)

class Reflector:

    def __init__(self, name: str, reflections: str):
        """Initialise a reflector

        Args:
            name (str): Name given to the reflector
            reflections (str): Permutation of English alphabet representing what
                letters reflect what other letters
        """
        self.name = name
        self.reflections = [ALPHABET.index(letter) for letter in reflections]


    def reflect(self, pin_in: int) -> int:
        """Reflect a given input

        Args:
            pin_in (int): Index of pin where electrical signal has been received

        Returns:
            int: Index of pin where electrical signal is output
        """
        return self.reflections[pin_in]

    
    def copy(self):
        return Reflector(
            self.name, ''.join([ALPHABET[c] for c in self.reflections])
        )

class Rotor:
    """Represents a rotor in the Enigma machine
    """
    
    def __init__(self, name: str, letters: str, turnovers: str):
        """Initialise the rotor

        Args:
            name (str): Name of the rotor
            letters (str): Permutation of ALPHABET representing wiring of rotor
            turnovers (str): Positions of the turnover notches on the rotor
        """
        self.name = name
        self.letters = letters
        self.turnover_letters = turnovers
        self.wiring = [ALPHABET.index(letter) for letter in letters]
        self.wiring_inverse = [
            self.wiring.index(pin_out) for pin_out in range(N)
        ]
        
        self.turnovers = [ALPHABET.index(turn) for turn in turnovers]
        self.ring_setting = 0
        self.offset = 0
        self.position = 0

    def configure(self, ring_setting_letter: str, offset_letter: str):
        """Configure this rotor

        Args:
            ring_setting_letter (str): Letter to adjust internal wiring to
            offset_letter (str): Letter to start from in encryption
        """
        try:
            self.ring_setting = ALPHABET.index(ring_setting_letter)
            self.offset = ALPHABET.index(offset_letter)
            self.position = (self.ring_setting - self.offset) % N
        except ValueError:
            print(ring_setting_letter, offset_letter)
            exit()

    def step(self):
        """Step one position
        """
        self.position = (self.position + 1) % N

    def unstep(self):
        """Step back one position
        """
        self.position = (self.position - 1) % N

    @property
    def turnover(self) -> bool:
        """Whether or not the pawl of the rotor is in the turnover position
        """
        return self.position in self.turnovers

    @property
    def did_turnover(self) -> bool:
        """Whether or not the rotor has just turned over
        """
        return (self.position - 1) % N in self.turnovers

    def signal_forward(self, sig_in: int) -> int:
        """Process a signal as it travels forward through the rotor

        Args:
            sig_in (int): Index of where the signal is received

        Returns:
            int: Index of where the signal is output
        """
        # Adjust for ring_setting
        pin_in = (sig_in + self.position) % N
        pin_out = self.wiring[pin_in]
        sig_out = (pin_out - self.position) % N
        return sig_out

    def signal_backward(self, sig_in: int) -> int:
        """Process a signal as it travels backward through the rotor

        Args:
            sig_in (int): Index of where the signal is received

        Returns:
            int: Index of where the signal is output
        """
        # Adjust for ring_setting
        pin_in = (sig_in + self.position) % N
        pin_out = self.wiring_inverse[pin_in]
        sig_out = (pin_out - self.position) % N
        return sig_out

    def copy(self):
        """Return an exact copy of this rotor
        """
        new_rotor = Rotor(self.name, self.letters, self.turnover_letters)
        new_rotor.configure(
            ALPHABET[self.ring_setting],
            ALPHABET[self.offset]
        )
        return new_rotor


class EnigmaMachine:
    """Represents an Enigma machine with a number of rotors and a reflector
    """

    def configure(
        self, rotors: list, reflector: Reflector, plugboard_pairs: list
    ):
        """Configure the machine with the given settings

        Args:
            rotors (list): List of rotors from right to left
            reflector (Reflector): Reflector to use
            plugboard_pairs (list): Pairs of letters use for the plugboard

        Raises:
            ValueError: You've entered an invalid plugboard setting
        """
        self.rotors: list[Rotor] = rotors
        self.reflector = reflector
        self.plugboard_pairs = {}
        for letter_a, letter_b in plugboard_pairs:
            a = ALPHABET.index(letter_a)
            b = ALPHABET.index(letter_b)
            if a in plugboard_pairs or b in plugboard_pairs:
                raise ValueError(
                    "You've entered duplicate values for the plugboard pairs"
                )
            elif a == b:
                raise ValueError("Plugboard cannot connect a letter to itself")
            self.plugboard_pairs[a] = b
            self.plugboard_pairs[b] = a
        
        # Unsteckered pairs
        for i in range(N):
            if i not in self.plugboard_pairs:
                self.plugboard_pairs[i] = i

        # Create copies of rotors to reset
        self.initial_rotors = [r.copy() for r in rotors]
        
    def step(self):
        """Step the machine forward one step
        """
        # Double stepping affects middle rotors, so treat those separately
        # Start with left and work back, checking if they should be advanced
        if self.rotors[-2].turnover:
            self.rotors[-1].step()
        
        # Middle rotors in reverse order
        for r in range(len(self.rotors)-2, 1, -1):
            if self.rotors[r-1].turnover or self.rotors[r].turnover:
                self.rotors[r].step()
        
        # First rotor always steps
        self.rotors[0].step()

    def unstep(self):
        """Reverse the stepping process
        """
        # Since this is in reverse, we need to start from the right, then check 
        # if we had double-stepped, and undo that
        self.rotors[0].unstep()

        for r in range(1, len(self.rotors)-2, -1):
            if self.rotors[r-1].turnover or self.rotors[r].did_turnover:
                self.rotors[r].unstep()
        
        if self.rotors[-2].turnover:
            self.rotors[-1].unstep()

    def encrypt_lettercode(self, lettercode: int) -> str:
        """Encrypt a single letter (integer representation)

        Args:
            lettercode (int): Input signal representing letter

        Returns:
            int: Signal output
        """
        # rotors -> reflector -> rotors
        for rotor in self.rotors:
            lettercode = rotor.signal_forward(lettercode)
        lettercode = self.reflector.reflect(lettercode)
        for rotor in self.rotors[::-1]:
            lettercode = rotor.signal_backward(lettercode)

        return lettercode

    def encrypt(self, plaintext: str) -> str:
        """Encrypts a message

        Args:
            plaintext (str): Message to encrypt

        Returns:
            str: Encrypted message
        """
        plaintext_upper = plaintext.upper()
        ciphertext = ""
        for letter in plaintext_upper:
            lettercode = ALPHABET.index(letter)
            self.step()
            lettercode = self.plugboard_pairs[lettercode]
            lettercode = self.encrypt_lettercode(lettercode)
            lettercode = self.plugboard_pairs[lettercode]
            ciphertext += ALPHABET[lettercode]
        return ciphertext

    def reset(self):
        """Reset rotor positions to initial settings
        """
        self.rotors = [r.copy() for r in self.initial_rotors]

    def copy(self):
        """Create an exact copy of the enigma machine in it's current state
        """
        machine = EnigmaMachine()
        machine.configure(self.rotors, self.reflector, self.plugboard_pairs)
        return machine


ROTORS = {
    'I': Rotor('I', 'EKMFLGDQVZNTOWYHXUSPAIBRCJ', 'Q'),
    'II': Rotor('II', 'AJDKSIRUXBLHWTMCQGZNPYFVOE', 'E'),
    'III': Rotor('III', 'BDFHJLCPRTXVZNYEIWGAKMUSQO', 'V'),
    'IV': Rotor('IV', 'ESOVPZJAYQUIRHXLNFTGKDCMWB', 'J'),
    'V': Rotor('V', 'VZBRGITYUPSDNHLXAWMJQOFECK', 'Z'),
    # 'VI': Rotor('VI', 'JPGVOUMFYQBENHZRDKASXLICTW', 'ZM'),
    # 'VII': Rotor('VII', 'NZJHGRCXMYSWBOUFAIVLPEKQDT', 'ZM'),
    # 'VIII': Rotor('VIII', 'FKQHTLXOCBJSPDZRAMEWNIUYGV', 'ZM')
}
REFLECTORS = {
    'B': Reflector('B', 'YRUHQSLDPXNGOKMIEBFZCWVJAT'),
    # 'C': Reflector('C', 'FVPJIAOYEDRZXWGCTKUQSBNMHL'),
    # 'B-Thin': Reflector('B-Thin', 'ENKQAUYWJICOPBLMDXZVFTHRGS'),
    # 'C-Thin': Reflector('C-Thin', 'RDOBJNTKVEHMLFCWZAXGYIPSUQ')
}
