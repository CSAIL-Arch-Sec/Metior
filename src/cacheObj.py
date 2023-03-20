import uuid

class cacheObj:

    def __init__(self, dagName, dagDict=None, attackerDict=None, key=None):
        self.victDAG = dagName
        if dagDict is not None:
            self.victDict = dagDict

        self.attackerDict = attackerDict

        self.cacheType = 0
        self.numLines = 2048

        self.key = key

        self.lineSize = 64

        self.associativity = 16
        self.sameset = 0
        self.subSectionLines = 64
        self.numPrime = 2

        self.numHG = 16

        self.numExtraPerSet = 6

        self.flush = 1
        self.randomPrime = 0

        self.debug = 0
        self.iterations = 200
        



    def info(self):
        return self.__dict__
    

