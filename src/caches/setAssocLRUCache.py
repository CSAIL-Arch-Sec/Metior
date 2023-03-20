import random
import numpy as np

cache_debug = False

class setAssocLRUCache:
    def __init__(self, numLines, associativity, lineSize):
        self.numLines = numLines
        self.associativity = associativity
        self.lineSize = lineSize 

        self.tagStore = np.ones((int(numLines/associativity), associativity), dtype=np.int32) * -1
        self.LRUStore = np.zeros((int(numLines/associativity), associativity), dtype=np.int32) 

    def clearCache(self):
        self.tagStore = np.ones((int(self.numLines/self.associativity), self.associativity), dtype=np.int32) * -1
        self.LRUStore = np.zeros((int(self.numLines/self.associativity), self.associativity), dtype=np.int32) 

    def getTag(self, addr):
        return int(addr / (self.lineSize * (self.numLines / self.associativity)))

    def getSet(self, addr):
        return int((addr / self.lineSize) % (self.numLines / self.associativity))

    def cacheAccess(self, addr):
        tag = self.getTag(addr)
        setIndex = self.getSet(addr)
        for way_id in range(self.associativity):
            if tag == self.tagStore[setIndex, way_id]:
                self.setLRU(setIndex, way_id)
                return True
        
        return False


    def cacheRepl(self, addr):
        assert(self.cacheAccess(addr) is False)
        
        setIndex = self.getSet(addr)

        for way_id in range(self.associativity):
            if self.LRUStore[setIndex, way_id] == 0:
                self.setLRU(setIndex, way_id)
                self.tagStore[setIndex][way_id] = self.getTag(addr)
                return 
        
        replWay = random.randint(0, self.associativity-1)
        self.setLRU(setIndex, replWay)
        self.tagStore[setIndex][replWay] = self.getTag(addr)
        return


    def setLRU(self, setIndex, way_id):
        ## if all bits are 1, reset all to 0
        i = 0
        while i < self.associativity:
            if self.LRUStore[setIndex, i] == 0:
                break
            i += 1

        assert(i <= self.associativity)
        if i == self.associativity:
            # need to reset all LRU bits
            for j in range(self.associativity):
                self.LRUStore[setIndex, j] = 0
       
        #set the current address as most recently used
        self.LRUStore[setIndex, way_id] = 1
        return
