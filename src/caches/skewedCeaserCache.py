#!/usr/bin/python3

import numpy
from random import random, randint, seed, randrange
from Crypto.Random import get_random_bytes
from Crypto.Cipher import AES
from Crypto.Util import Padding
#from lib_qarma64 import qarma64
from cache import Cache
from cache import cache_debug

class skewedCeaserCache(Cache):

    def __init__(self, numLines, associativity, lineSize, numHG=16, key=None, debug=False):

        self.randomReplacement = False

        num_ways = associativity
        num_sets = int(numLines / associativity)
        num_banks = numHG

        self.lineSize = lineSize
        self.numLines = numLines
        self.associativity = associativity
        
        super().__init__(num_ways, num_sets, num_banks)
        self.LRUs = numpy.zeros((num_ways, num_sets), dtype=int)

        self.lastLoc = None
        self.lastAddr = None

        # NOTE: in ScatterCache, some hash functions are used
        # Here, we simply do an xor operation
        # for way i, the selected set will be
        # (addr>>block_bits)%num_sets XOR key_i
        #self.ciphers = [None]*num_banks
        #for i in range(num_banks):
        #    key = get_random_bytes(16)
        #    self.ciphers[i] = AES.new(key, AES.MODE_ECB)
        #print(self.ciphers)
        # For qarma64_SCv2, random tweak and key
        #self.qarma64_tweak = get_random_bytes(8)
        #self.qarma64_key = get_random_bytes(16)
        # For AES_SCv2
        if key == None:
            #self.encryption_key = "1234567890123456".encode('ascii')
            self.encryption_key = int.from_bytes(get_random_bytes(16), byteorder='big')
            self.AES_SCv2_cipher = AES.new(self.encryption_key.to_bytes(16, byteorder='big'), AES.MODE_ECB)
        else:
            self.encryption_key = key
            self.AES_SCv2_cipher = AES.new(self.encryption_key.to_bytes(16, byteorder='big'), AES.MODE_ECB)
        
        self.info()


    # Wrapper Functions

    def cacheAccess(self, addr, debug=False):
        #print("Accessing addr: %d" % (addr))
        result, loc = self.probe(addr)
        self.lastAddr = addr
        self.lastLoc = loc
        
        # if result: print("HIT")
        # else: print("MISS")

        # print("Possible Slots: ")
        # print(self.get_slots(addr))

        # print("Chosen:")
        # print(self.lastLoc)

        return result

    def cacheRepl(self,addr,debug=False):
        assert(self.lastAddr == addr)
        self.insert(addr, self.lastLoc)

    def clearCache(self, debug):
        self.LRUs = numpy.zeros((self.num_ways, self.num_sets), dtype=int)
        self.tags = numpy.full((self.num_ways, self.num_sets), -1, dtype=int)

    def info(self):
        print("Skewed cache!")
        print("number of ways = ", self.num_ways,
                "; number of sets = ", self.num_sets,
                "; number of banks = ", self.num_banks)
        print("size = ", self.num_ways*self.num_sets*64*1.0/2**20, "MB")

    def get_slots(self, addr): # return all possible slots the address could map to
        slots = set()
        for i in range(self.num_banks):
            slots.add((i * self.num_sets + self.get_set(addr, i)))
        return slots
    
    def get_set(self, addr):
        assert(0 and \
            "Must provide the set_id to obtain set_index in SkewedCeaserCache.")

    #encription as SCv2 in scatter cache
    def get_set(self, addr, bank_id):
        # Plaintext: tag(42 - log(num_sets)), bank(log(num_banks)), padding
        # Use block cipher QARMA-64 or AES get ciphertext with random tweak and key
        # Set number: original index XOR (ciphertext % num_sets)
        assert(addr >= 0)
        index_bits = numpy.log2(self.num_sets)
        bank_bits = numpy.log2(self.num_banks)
        assert(index_bits % 1 == 0)
        assert(bank_bits % 1 == 0)
        index_bits = int(index_bits)
        bank_bits = int(bank_bits)
        assert(42 - index_bits + bank_bits <= 48)

        # get plain text
        tag = addr >> (self.block_bits+index_bits)
        index = (addr>>self.block_bits) % self.num_sets
        plaintext = ((tag<<bank_bits) + bank_id).to_bytes(6, byteorder='big', signed=False)
        plaintext = Padding.pad(plaintext, 16)
        # call encryption with qarma64, but too slow
        #ciphertext = qarma64(plaintext.hex(), self.qarma64_tweak.hex(), self.qarma64_key.hex(), encryption=True, rounds=5)
        #ciphertext = int(ciphertext, 16)
        # call encryption with AES
        ciphertext = self.AES_SCv2_cipher.encrypt(plaintext)
        ciphertext = int.from_bytes(ciphertext, byteorder='big')
        return index ^ (ciphertext % self.num_sets)
    

    # test whether address a and b soft conflict or not
    # soft conflict: there exists a bank i, where
    # set_index(a, i) == set_index(b, i)
    # return the pairs of bank ids and sets that soft conflicts if exists
    def get_soft_conflict_banks(self, a, b):
        conflicts = set()
        for i in range(self.num_banks):
            conflict_set = self.get_set(a,i)
            if conflict_set == self.get_set(b, i):
                conflicts.add((i, conflict_set))
        return conflicts

    def is_soft_conflict(self, a, b):
        for i in range(self.num_banks):
            if self.get_set(a, i) == self.get_set(b, i):
                return True
        return False

    def set_lru_bits(self, way_id, set_index):
        self.LRUs[way_id, set_index] = 1

        ## if all bits are 1, reset all to 0
        i = 0
        for way in [j+int(way_id/self.num_ways_per_bank)*self.num_ways_per_bank for j in range(self.num_ways_per_bank)]:
            if self.LRUs[way, set_index] == 1:
                i +=1

        if i == self.num_ways_per_bank:
            # need to rest all LRU bits
            for way in [j+int(way_id/self.num_ways_per_bank)*self.num_ways_per_bank for j in range(self.num_ways_per_bank)]:
                self.LRUs[way, set_index] = 0

    def probe(self, addr):
        ## The tag is different from the basic set-associative cache
        addr_tag = self.get_tag(addr)
        for i in range(self.num_banks):
            set_index = self.get_set(addr, i)
            for w in range(self.num_ways_per_bank):
                way_id = w+(i*self.num_ways_per_bank)
                if self.tags[way_id, set_index] == addr_tag:
                    if not self.randomReplacement: self.set_lru_bits(way_id, set_index)
                    return (True, (way_id, set_index))

        # TODO: need to discuss:
        # using super random replacement is not good for cache performance
        # but easy for attacker? Maybe?

        # randomly choose the bank to put data in
        bank_id = randint(0,self.num_banks-1)
        # find the set this addr maps to within the bank
        set_index = self.get_set(addr, bank_id)

        ## For each bank, we use LRU to choose a way
        if not self.randomReplacement: 
            for i in [j+bank_id*self.num_ways_per_bank for j in range(self.num_ways_per_bank)]:
                if self.tags[i, set_index] == -1:
                    self.set_lru_bits(i, set_index)
                    return (False, (i, set_index))

            for i in [j+bank_id*self.num_ways_per_bank for j in range(self.num_ways_per_bank)]:
                if self.LRUs[i, set_index] == 0:
                    self.set_lru_bits(i, set_index)

                    return (False, (i, set_index))

            self.set_lru_bits(bank_id*self.num_ways_per_bank, set_index)

            return(False, (bank_id*self.num_ways_per_bank, set_index))
        else:
            return (False, (randrange(0, self.num_ways_per_bank) + bank_id * self.num_ways_per_bank,set_index))




if __name__ == "__main__":
    seed(1)
    example = skewedCeaserCache(2,2,64,2)
    example.info()

    addr = 198783
    print(example.cacheAccess(addr))
    example.cacheRepl(addr)

    print(example.cacheAccess(addr))
