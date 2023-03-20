import random
import numpy as np

REPL_DEBUG = False


class setAssocRandomCache:
    def __init__(self, numLines, associativity, lineSize):
        self.numLines = numLines
        self.associativity = associativity
        self.lineSize = lineSize 

        self.tagStore = np.ones((int(numLines/associativity), associativity), dtype=np.int32) * -1

    def clearCache(self):
        self.tagStore = np.ones((int(self.numLines/self.associativity), self.associativity), dtype=np.int32) * -1

    def getTag(self, addr):
        return int(addr / (self.lineSize * (self.numLines / self.associativity)))

    def getSet(self, addr):
        return int((addr / self.lineSize) % (self.numLines / self.associativity))

    def cacheAccess(self, addr):
        for tag in self.tagStore[self.getSet(addr)]:
            if tag == self.getTag(addr):
                return True

        return False

    def cacheRepl(self, addr):
        assert(self.cacheAccess(addr) is False)
        
        replWay = random.randint(0, self.associativity-1)
        self.tagStore[self.getSet(addr)][replWay] = self.getTag(addr)
        return


