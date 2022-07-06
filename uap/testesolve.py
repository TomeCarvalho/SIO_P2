from bitstring import BitArray
import hashlib, random

server = BitArray('0x3c7b9c9f7212994441a677e6bf6b4c07')
local = BitArray('0x4a8ee31d89ef1dd39b8ee54ea7a4b81d')
# local = BitArray('0x3c7b9c9f7212994441a677e6bf6b4c07')



def solve_challenge(challenge, passw):
    
    # print("init func")
    # hash challenge (seed) --> int
    # hash password --> ArrayBit
    # xor both --> ArrayBit
    # n1%2 == 0 --> 0/1

    hash_challenge = BitArray(hashlib.md5(bin(challenge).encode('utf-8')).digest())
    # print((hash_challenge & passw).bin)
    return sum(hash_challenge | passw) % 2


nTrues = 0
n = 1000

for i in range(n):
    challenge = random.randint(0, 999999)
    # print(solve_challenge(challenge, server))
    # print(solve_challenge(challenge, local))
    boo = solve_challenge(challenge, server) == solve_challenge(challenge, local)
    # print(boo)
    if boo: nTrues += 1
    # print("-------------")

print(f'{nTrues = }')
print(f'{(n - nTrues) = }')
