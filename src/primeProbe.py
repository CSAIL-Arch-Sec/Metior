import random

HIT_DEBUG = False
NUM_ITERS = 5000
VIC_RANGE_START = 999999
MAX_CACHE_LINES = 65536 # cache size = 4MB 

def warmup(cache):
    startLine = cache.numLines * 3
    for i in range(int(cache.numLines * 2)):
        if not cache.cacheAccess( (startLine+i) * cache.lineSize):
            cache.cacheRepl( (startLine+i) * cache.lineSize )

def prime(cache, numAcc, sameSet, randomPrime, randomBase,\
          iternum, primenum, numprime, debug):
    
    numMiss = 0
    for accNum in range(int(numAcc)):
        if randomPrime == False:
            if sameSet == False:
                primeLine = accNum * cache.lineSize
            else:
                primeLine = accNum * cache.lineSize * (cache.numLines / cache.associativity)
        else:
            primeLine = (randomBase + accNum) * cache.lineSize 
            #print("randomBase: ", randomBase,
            #      "; accNum: ", accNum,
            #      "; randomBase + accNum: ", randomBase + accNum)

        assert(primeLine/cache.lineSize < VIC_RANGE_START) 
        global_accNum = iternum*(numprime+1)*numAcc + primenum*numAcc + accNum
        if(debug):
            print("----------------------------------------------")
            if(primenum != numprime):
                print("iteration:%d, prime: %d, accessnum:%d: address %d"\
                    %(iternum, primenum, global_accNum, primeLine))
            else:
                print("iteration:%d, PROBE, accessnum:%d: address %d"\
                    %(iternum, global_accNum, primeLine))
        
        if cache.cacheAccess(primeLine, debug):
            if(debug):
                if(primenum != numprime):
                    print("PRIME HIT")
                else:
                    print("PROBE HIT")
        else:
            if(debug):
                if(primenum != numprime):
                    print("PRIME MISS")
                else:
                    print("PROBE MISS")
            cache.cacheRepl(primeLine, debug)
            numMiss += 1
    
    return numMiss

def prime_custom(cache, attackerDict, sameSet, randomPrime, randomBase,\
          iternum, primenum, numprime, debug):
    
    numMiss = 0
    numAcc = len(attackerDict)
    for accNum in range(len(attackerDict)):

        primeLine = attackerDict[accNum]

        #assert(primeLine/cache.lineSize < VIC_RANGE_START) 
        global_accNum = iternum*(numprime+1)*numAcc + primenum*numAcc + accNum
        if(debug):
            print("----------------------------------------------")
            if(primenum != numprime):
                print("iteration:%d, prime: %d, accessnum:%d: address %d"\
                    %(iternum, primenum, global_accNum, primeLine))
            else:
                print("iteration:%d, PROBE, accessnum:%d: address %d"\
                    %(iternum, global_accNum, primeLine))
        
        if cache.cacheAccess(primeLine, debug):
            if(debug):
                if(primenum != numprime):
                    print("PRIME HIT")
                else:
                    print("PROBE HIT")
        else:
            if(debug):
                if(primenum != numprime):
                    print("PRIME MISS")
                else:
                    print("PROBE MISS")
            cache.cacheRepl(primeLine, debug)
            numMiss += 1
    
    return numMiss

def simpleVictim(cache, numAcc, randomVictim, iternum, debug):
    numMiss = 0
    for i in range(numAcc):
        # Ensure that there are no address collisions between the victim and attacker
        if randomVictim == False:
            vicLine = VIC_RANGE_START + i
        else:    
            vicLine = random.randint(VIC_RANGE_START,VIC_RANGE_START+cache.numLines-1)
            if (debug):
                print("----------------------------------------------")
                print("iteration: %d, VICTIM, address %d" % (iternum, vicLine * cache.lineSize))
        if not cache.cacheAccess(vicLine * cache.lineSize, debug):
            if (debug): print("VICTIM MISS")
            cache.cacheRepl(vicLine * cache.lineSize, debug)
            numMiss += 1
        else:
            if (debug): print("VICTIM HIT")
    
    return numMiss

def victim(cache, victDict, debug):
    numMiss = 0
    for _,victAddr in victDict.items():
        # print(victAddr)
        # print("Accessing vict addr: %x" % (victAddr))
        if not cache.cacheAccess(victAddr, debug):
            # print("VICTIM MISS")
            cache.cacheRepl(victAddr, debug)
            numMiss += 1
        else:
            pass
            # print("VICTIM HIT")
    
    return numMiss

def warmup_then_attack(cache, subsectionAcc, victimDict, numPrime, iterations,\
                       sameSet=False, flush=True, randomPrime=False,\
                       debug=False):
    missArray = []
    primeParentArray = []

    # print("VICTIM DICT:")
    # print(list(victimDict.values())[0:5])
    #subsectionAcc = cache.numLines / subsection
    for iternum in range(iterations):
        if(debug):
            print("##############################")
            print("######ITERATION %d of %d######" % (iternum+1, iterations))
            print("##############################")
        
        primeMissArray = []
        #warmup(cache)
        
        randomBase = random.randint(0, VIC_RANGE_START - MAX_CACHE_LINES - 1)
        for primenum in range(numPrime):
            if(debug):
                print("###PRIME %d of %d###" % (primenum+1, numPrime))
            primeMissArray.append(prime(cache, subsectionAcc, sameSet, randomPrime, randomBase,\
                                        iternum, primenum, numPrime, debug))
        primeParentArray.append(primeMissArray)
        
        if (debug):
            print("###VICTIM###")
        victim(cache, victimDict, debug)
        if (debug):
            print("###PROBE###")
        missArray.append(prime(cache, subsectionAcc, sameSet, randomPrime, randomBase,\
                               iternum, numPrime, numPrime, debug))

        if flush: cache.clearCache(debug)
    cost = (numPrime + 1) * subsectionAcc #+ numVicAcc

    return missArray, cost, primeParentArray

def warmup_then_attack_custom(cache, attackerDict, victimDict, numPrime, iterations,\
                       sameSet=False, flush=True, randomPrime=False,\
                       debug=False):
    missArray = []
    primeParentArray = []

    # print("VICTIM DICT:")
    # print(list(victimDict.values())[0:5])
    #subsectionAcc = cache.numLines / subsection
    for iternum in range(iterations):
        if(debug):
            print("##############################")
            print("######ITERATION %d of %d######" % (iternum+1, iterations))
            print("##############################")
        
        primeMissArray = []
        #warmup(cache)
        
        randomBase = random.randint(0, VIC_RANGE_START - MAX_CACHE_LINES - 1)
        for primenum in range(numPrime):
            if(debug):
                print("###PRIME %d of %d###" % (primenum+1, numPrime))
            primeMissArray.append(prime_custom(cache, attackerDict, sameSet, randomPrime, randomBase,\
                                        iternum, primenum, numPrime, debug))
        primeParentArray.append(primeMissArray)
        
        if (debug):
            print("###VICTIM###")
        victim(cache, victimDict, debug)
        if (debug):
            print("###PROBE###")
        missArray.append(prime_custom(cache, attackerDict, sameSet, randomPrime, randomBase,\
                               iternum, numPrime, numPrime, debug))

        if flush: cache.clearCache(debug)
    cost = (numPrime + 1) * len(attackerDict) #+ numVicAcc

    return missArray, cost, primeParentArray
