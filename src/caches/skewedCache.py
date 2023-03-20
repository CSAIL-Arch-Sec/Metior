import random
import numpy as np
import math
from Crypto.Random import get_random_bytes
from Crypto.Cipher import AES
from Crypto.Util import Padding

REPL_DEBUG = False


#Assume one way per HashGroup for now
#i.e., associativity == # of HGs
class skewedCache:

    def __init__(self, numLines, associativity, lineSize, numHG=16, debug=False):
        self.lineSize = lineSize
        self.numLines = numLines
        self.block_bits = int(math.log2(numLines))
        self.associativity = associativity
        self.num_sets = int(numLines/associativity)
        
        self.numHG = numHG
        self.num_way_per_HG = int(associativity/numHG)

        self.tagStore = np.ones((int(numLines/associativity), associativity), dtype=np.int32) * -1

        self.LRUStore = np.zeros((int(numLines/associativity), associativity), dtype=np.int32) 


        self.encryption_key = dict() 
        #for HG_id in range(associativity):
        for HG_id in range(numHG):
            self.encryption_key[HG_id] = int.from_bytes(get_random_bytes(16), byteorder='big')

        self.AES_SCv2_cipher = dict()
        #for HG_id in range(associativity):
        for HG_id in range(numHG):
            self.AES_SCv2_cipher[HG_id] = AES.new(self.encryption_key[HG_id].to_bytes(16, byteorder='big'), AES.MODE_ECB)
        if(debug):
            print("INTIALIZING CACHE:")
            print("self.lineSize  " +   str(self.lineSize))
            print("self.numLines  " +   str(self.numLines))
            print("self.block_bits" +   str(self.block_bits))
            print("self.associativity  " +   str(self.associativity))
            print("self.numHG  " +   str(self.numHG))
            print("self.num_way_per_HG  " +   str(self.num_way_per_HG))
            print("self.tagStore  " +   str(self.tagStore))
            print("self.LRUStore  " +   str(self.LRUStore))
            print("self.encryption_key  " +   str(self.encryption_key))
            print("self.AES_SCv2_cipher  " +   str(self.AES_SCv2_cipher))



    def clearCache(self, debug=False):
        self.tagStore = np.ones((int(self.numLines/self.associativity), self.associativity), dtype=np.int32) * -1
        self.LRUStore = np.zeros((int(self.numLines/self.associativity), self.associativity), dtype=np.int32) 
        if(debug):
            print("CACHE CLEARED")
            print("self.tagStore: "+str(self.tagStore))
            print("self.LRUStore: "+str(self.LRUStore))

    # SCATTER-CACHE stores the index bits from the physical address in addition to the tag bits
    def getTag(self, addr):
        # keep the setIndex in the tag 
        return int(addr / self.lineSize )
        # return (tag | setIndex)

    def getSet(self, addr):
        assert(0 and \
            "Must provide the HG_id to obtain set_index in skewedCache.")


    #encription as SCv2 in scatter cache
    def getSet(self, addr, HG_id):
        # Plaintext: (tag | HG_id | padding)  , 48 bits
        # Use AES to  get ciphertext
        # new setIndex: original setIndex XORed with (ciphertext % numSets)
        
        # get plaintext
        tag = int(addr / (self.lineSize * (self.numLines / self.associativity)))
        #tag = self.getTag(addr) # DON'T INCORPORATE SET INDEX HERE!
        setIndex = int((addr / self.lineSize) % (self.numLines / self.associativity))

        plaintext = ((tag * self.numHG) + HG_id).to_bytes(6, byteorder='big', signed=False)
        plaintext = Padding.pad(plaintext, 16)
        
        # call encryption with AES
        ciphertext = self.AES_SCv2_cipher[HG_id].encrypt(plaintext)
        ciphertext = int.from_bytes(ciphertext, byteorder='big')
        #print("Addr: " + str(addr) + " Out: " + str(int(setIndex ^ int(ciphertext % int(self.numLines / self.associativity)))) + " Cipher: " + str(ciphertext) + " plain " + str(plaintext) + " setindex " + str(setIndex))
        return int(setIndex ^ int(ciphertext % int(self.numLines / self.associativity)))

    def cacheAccess(self, addr, debug):
        #for HG_id in range(self.associativity):
        #    if self.tagStore[self.getSet(addr, HG_id), HG_id] == self.getTag(addr):
        #        return True
        #    
        #return False
        if(debug):
            tag_id = self.getTag(addr)
            print("addr: %d, tag = %d" % (addr, tag_id))
            for HG_id in range(self.numHG):
                set_in_HG = self.getSet(addr, HG_id)
                print("--HG_id: " + str(HG_id))
                print("----set_in_HG: " + str(set_in_HG) + " HG_way_base: " + str(HG_id * self.num_way_per_HG))
            print("tagStore:" + str(self.tagStore))
            print("LRUStore:" + str(self.LRUStore))

        for HG_id in range(self.numHG):
            set_in_HG = self.getSet(addr, HG_id)
            for way_in_HG in range(self.num_way_per_HG):
                global_way_id = way_in_HG + (HG_id * self.num_way_per_HG)
                if self.tagStore[set_in_HG, global_way_id] == self.getTag(addr):
                    self.setLRU(set_in_HG, global_way_id)
                    return True
        return False

    def cacheRepl(self, addr, debug):
        #assert(self.cacheAccess(addr) is False) -- adds noise to the debug print,,
        if(debug):
            print("Before Replacement: tagStore: "+str(self.tagStore))
            print("Before Replacement: LRUStore: "+str(self.LRUStore))

        #replWay = random.randint(0, self.associativity-1)
        #self.tagStore[self.getSet(addr, replWay)][replWay] = self.getTag(addr)
        #return 
        replHG = random.randint(0, self.numHG - 1)
        set_in_HG = self.getSet(addr, replHG)
        if(debug):
            print("randomly selected HG for replacement: %d" % replHG)
            print("==> HG %d : encrypted set == %d" % (replHG, set_in_HG))

        for way_in_HG in range(self.num_way_per_HG):
            global_way_id = way_in_HG + (replHG * self.num_way_per_HG)
            if self.LRUStore[set_in_HG, global_way_id] == 0:
                if(debug):
                    evictedAddr = self.tagStore[set_in_HG, global_way_id]
                    evictedAddr *= self.lineSize
                    print("LRU Replacement: Evicting Addr: %d" % evictedAddr)
                self.setLRU(set_in_HG, global_way_id)
                self.tagStore[set_in_HG, global_way_id] = self.getTag(addr)
                if(debug):
                    print("After: LRU Replacement: tagStore: "+str(self.tagStore))
                    print("After: LRU Replacement: LRUtore: "+str(self.LRUStore))
                return


        replWay_in_HG = random.randint(0, self.num_way_per_HG-1)
        repl_globalWay = replWay_in_HG + (replHG * self.num_way_per_HG)
        if(debug):
            evictedAddr =  self.tagStore[set_in_HG, repl_globalWay]  
            evictedAddr *= self.lineSize
            print("Random Replacement: Evicting Addr: %d" % evictedAddr) 
        self.setLRU(set_in_HG, repl_globalWay)
        self.tagStore[set_in_HG, repl_globalWay] = self.getTag(addr)
        if(debug):
            print("After: Random Replacement: tagStore: "+str(self.tagStore))
            print("After: Random Replacement: LRUStore: "+str(self.LRUStore))
        return

    def setLRU(self, set_in_HG, global_way_id):
        ## if all bits are 1, reset all to 0
        i = 0
        HG_id = int(global_way_id / self.num_way_per_HG)
        HG_way_base = HG_id * self.num_way_per_HG
        while i < self.num_way_per_HG:
            if self.LRUStore[set_in_HG, HG_way_base + i] == 0:
                break
            i+=1

        assert(i <= self.num_way_per_HG)
        if i == self.num_way_per_HG:
            # need to reset all LRU bits
            for j in range (self.num_way_per_HG):
                self.LRUStore[set_in_HG, HG_way_base + j] = 0

        #set the current address as the most recently used
        self.LRUStore[set_in_HG, global_way_id] = 1
        return

