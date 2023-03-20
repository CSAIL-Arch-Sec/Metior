import random
import numpy as np

REPL_DEBUG = False

class mirageCache():

    def __init__(self, numLines, associativity, lineSize, numExtraPerSet=16, debug=False):
        self.numLines = numLines
        self.associativity = associativity
        self.lineSize = lineSize
        self.numExtraPerSet = numExtraPerSet

        self.numSets = self.numLines // self.associativity
        #TODO: Check me
        #self.tagMask = self.lineSize * self.numSets
        self.tagMask = self.lineSize

        self.tagStore = np.ones((2, int(numLines/associativity), associativity+numExtraPerSet), dtype=np.int32) * -1
        self.forwardMap = np.ones((2, int(numLines/associativity), associativity+numExtraPerSet), dtype=np.int32) * -1
        self.reverseMap = np.ones((numLines), dtype=np.int32) * -1
        if(debug):
            print("INTIALIZING CACHE:")
            print("self.lineSize  " +   str(self.lineSize))
            print("self.numLines  " +   str(self.numLines))
            print("self.associativity  " +   str(self.associativity))
            print("self.numExtraPerSet  " +   str(self.numExtraPerSet))
            print("self.tagStore  " +   str(self.tagStore))
            print("self.forwardMap  " +   str(self.forwardMap))
            print("self.reverseMap  " +   str(self.reverseMap))

    def clearCache(self, debug=False):
        self.tagStore = np.ones((2, int(self.numLines/self.associativity), self.associativity+self.numExtraPerSet), dtype=np.int32) * -1
        self.forwardMap = np.ones((2, int(self.numLines/self.associativity), self.associativity+self.numExtraPerSet), dtype=np.int32) * -1
        self.reverseMap = np.ones((self.numLines), dtype=np.int32) * -1

    def getTag(self, addr):
        return addr // self.tagMask

    def getSet(self, addr, skew):
        random.seed((addr // self.lineSize) % (self.numSets) + skew*self.numSets)
        return random.randint(0, self.numSets-1)

    def cacheAccess(self, addr, debug):
        # if(debug):
        #     tag_id = self.getTag(addr)
        #     set_id = self.getSet(addr)
        #     tags_in_set = self.tagStore[set_id]
        #     print("addr = %d, tag= %d, set = %d" % (addr, tag_id, set_id))
        #     print("set " + str(set_id) + ": tags: " + str(tags_in_set))

        tag = self.getTag(addr)

        if tag in self.tagStore[0][self.getSet(addr, 0)]:
            return True

        if tag in self.tagStore[1][self.getSet(addr, 1)]:
            return True

        return False

    def cacheRepl(self, addr, debug):
        #assert(self.cacheAccess(addr) is False) -- adds noise to the debug print,,
        if(debug):
            print("Before Replacement: tagStore: "+str(self.tagStore))
            print("Before Replacement: forwardMap: "+str(self.forwardMap))
            print("Before Replacement: reverseMap: "+str(self.reverseMap))

        random.seed()
        replLine = random.randint(0,self.numLines-1)
        if debug: print("Replacing line: %d" % (replLine))
        replTarget = self.reverseMap[replLine]
        if debug: print("ReplLine/ReplTarget: %d/%d" % (replLine, replTarget))

        if replTarget != -1:
            skew = 0
            index = np.where(self.tagStore[0][self.getSet(replTarget,0)] == self.getTag(replTarget))[0]
            if len(index) == 0:
                if debug: print("SKEW1")
                skew = 1
                index = np.where(self.tagStore[1][self.getSet(replTarget,1)] == self.getTag(replTarget))[0]
            # else:
            #     assert(len(np.where(self.tagStore[1][self.getSet(replTarget,1)] == self.getTag(replTarget))[0]) == 0)
            
            
            if len(index) == 0:
                raise ValueError('Reverse Target Not Found!')
            
            skewSet = self.getSet(replTarget,skew)

            if debug: 
                print("MATCHA?")
                print(self.tagStore[skew][skewSet][index[0]])
                print(self.getTag(replTarget))

            #assert(self.tagStore[skew][skewSet][index[0]] == self.getTag(replTarget))
            self.tagStore[skew][skewSet][index[0]] = -1

            if debug: 
                print("MATCHB?")
                print("OUTGOING FWMAP: %d, %d, %d, %d" % (skew, skewSet, index[0], self.forwardMap[skew][skewSet][index[0]]))
                print(self.forwardMap[skew][skewSet][index[0]])
                print(replLine)
            #assert(self.forwardMap[skew][skewSet][index[0]] == replLine)
            self.forwardMap[skew][skewSet][index[0]] = -1

        tag = self.getTag(addr)

        set0 = self.getSet(addr,0)
        set1 = self.getSet(addr,1)

        invalids0 = np.where(self.tagStore[0][set0] == -1)[0]
        invalids1 = np.where(self.tagStore[1][set1] == -1)[0]

        if len(invalids0) == 0 and len(invalids1) == 0:
            print("Set Conflict!")
            return
            #raise ValueError('Set Conflict!')

        selectedSkew = len(invalids0) < len(invalids1)
        if(debug):
            print("Selected Skew: %d/%d/%d" %(len(invalids0), len(invalids1), selectedSkew))

        if selectedSkew == 0:
            self.tagStore[0][set0][invalids0[0]] = tag
            self.forwardMap[0][set0][invalids0[0]] = replLine
            if debug: print("setting FWMAP: %d, %d, %d, %d" % (0, set0, invalids0[0], replLine))
        else:
            self.tagStore[1][set1][invalids1[0]] = tag
            self.forwardMap[1][set1][invalids1[0]] = replLine
            if debug: print("setting FWMAP: %d, %d, %d, %d" % (1, set1, invalids1[0], replLine))

        if debug: print("setting reverse map: %d, %d" %(replLine, addr))
        self.reverseMap[replLine] = addr

        if(debug):
            print("Selected Skew: %d" % (selectedSkew))
            print("Set0: %d, Set1: %d" % (set0, set1))
            print("After Replacement: tagStore: "+str(self.tagStore))
            print("After Replacement: forwardMap: "+str(self.forwardMap))
            print("After Replacement: reverseMap: "+str(self.reverseMap))

        # # Check that there is a free tag ==> If so, global random replacement
        # i = 0
        # for tag in self.tagStore[self.getSet(addr)]:
        #     if int(tag) == -1 :  # Global random replacment!
        #         if (replTarget != -1):  
        #             setID = int(replTarget / (self.associativity + self.numExtraPerSet))
        #             slotID = replTarget % (self.associativity + self.numExtraPerSet)
        #             if (debug): 
        #                 print("Global Line Eviction!")
        #                 print("Backwards replacement! Evicting: reverseMapIndex: %d, set: %d, way %d "\
        #                       % (replLine, setID, slotID))

        #             assert(self.forwardMap[setID][slotID] == replLine)
        #             self.tagStore[setID][slotID] = -1
        #             self.forwardMap[setID][slotID] = -1
                
        #         self.tagStore[self.getSet(addr)][i] = self.getTag(addr)
        #         self.forwardMap[self.getSet(addr)][i] = replLine
        #         self.reverseMap[replLine] = self.getSet(addr) * (self.associativity + self.numExtraPerSet) + i
        #         if(debug):
        #             print("after replacement: tagstore: "+str(self.tagStore))
        #             print("after replacement: forwardmap: "+str(self.forwardMap))
        #             print("after replacement: reversemap: "+str(self.reverseMap))
        #         return
        #     i += 1

        # #assert(False)
        # #No free tag in set ==> Set Associative Eviction 
        # replWay = random.randint(0, self.associativity + self.numExtraPerSet - 1) 
        # if (debug): 
        #     print("SAE: Set Associative Eviction!")
        #     print("Replacing: Set: %d, Way: %d, Tag: %d" \
        #            % (self.getSet(addr), replWay, self.tagStore[self.getSet(addr)][replWay]))
        
        # self.tagStore[self.getSet(addr)][replWay] = self.getTag(addr)
        # if(debug):
        #     print("aftre replacement: tagstore: "+str(self.tagStore))
        #     print("after replacement: forwardmap: "+str(self.forwardMap))
        #     print("after replacement: reversemap: "+str(self.reverseMap))

