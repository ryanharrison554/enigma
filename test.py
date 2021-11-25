from enigma import enigma

with open('in.txt') as infile:
    intext = infile.read()

plaintext = ''
for c in intext:
    if c.isalpha():
        plaintext += c.upper()

rotor_I = enigma.ROTORS['I'].copy()
rotor_II = enigma.ROTORS['II'].copy()
rotor_III = enigma.ROTORS['III'].copy()

rotor_I.configure('A', 'A')
rotor_II.configure('A', 'A')
rotor_III.configure('A', 'A')

machine = enigma.EnigmaMachine()
machine.configure([rotor_I, rotor_II, rotor_III], enigma.REFLECTORS['B'], [
    ('A', 'B'),
    ('C', 'D'),
    ('E', 'F'),
    ('G', 'H'),
    ('I', 'J'),
    ('K', 'L')
])

ciphertext = machine.encrypt(plaintext)

machine.reset()
print(ciphertext)