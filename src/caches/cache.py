#!/usr/bin/python3

import numpy
from random import random, randint, seed
from Crypto.Random import get_random_bytes
from Crypto.Cipher import AES
from Crypto.Util import Padding
from collections import defaultdict
from statistics import mean, stdev

cache_debug = False

class Cache:
    def __init__(self, num_ways, num_sets, num_banks):
        self.block_bits = 6 # assume the block size = 2**6
        self.num_ways = num_ways
        self.num_sets = num_sets
        self.num_banks = num_banks
        self.num_ways_per_bank = int(num_ways/num_banks)
        #initialize all the addresses in the cache as -1
        self.tags = numpy.full((num_ways, num_sets), -1, dtype=int)
        self.debug = 0
        if cache_debug == True:
            self.log = []

        ################ STATS ###################
        self.stat_track_trs = set()
        self.stat_track_candidates = set()

        # addrs evicted by the tr
        self.stat_cand_evicted_by_tr = set()
        # map from addr to addr, track edges between candidates
        self.stat_cand_evict_cand_edges = defaultdict(int)

        # track the number of accesses. including flushes
        self.stat_num_tr_accesses = 0
        self.stat_num_prune_accesses = 0
        self.stat_num_check_accesses = 0
        self.stat_num_candidate_flushes = 0
        self.stat_num_tr_flushes = 0
        self.stat_num_misses = 0

    ################ BEGIN STATS ###################
    def set_trs_to_track(self,track_trs):
        self.stat_track_trs = set(track_trs)

    def set_candidates_to_track(self,track_cand):
        self.stat_track_candidates = track_cand

    # FIX BUG: this tracking includes addresses that are evicted after being accessed
    # This should not form a chain
    #def track_cand_evictions(self,accessed, evicted):
    #    if self.stat_track_candidates is not None and self.stat_track_trs is not None:
    #        if evicted in self.stat_track_candidates:
    #            if accessed in self.stat_track_trs:
    #                self.stat_cand_evicted_by_tr.add(evicted)
    #            elif accessed in self.stat_track_candidates:
    #                self.stat_cand_evict_cand_edges[accessed] = evicted
    

    ## TODO all these are wrong be cause provate has no group access
    '''
    def track_cand_evictions(self, hit, accessed_addr, evicted_addr):
        if self.stat_track_candidates is not None and self.stat_track_trs is not None:
                ## count the addresses that miss the cache and are evicted by previous 
                ## candidate accesses
                #print(evicted_addr, accessed_addr)
            if hit and evicted_addr != -1:
                if evicted_addr in self.stat_track_candidates and accessed_addr in self.stat_track_trs:
                        self.stat_cand_evicted_by_tr.add(evicted_addr)
                        return
                if evicted_addr in accessed[i+1:]: #and evicted_addr in self.stat_track_candidates:
                    if accessed_addr in self.stat_track_trs: ##should not happen
                        self.stat_cand_evicted_by_tr.add(evicted_addr)
                    elif accessed_addr in self.stat_track_candidates:
                        self.stat_cand_evict_cand_edges[accessed_addr] = evicted_addr
    '''
    def get_len_cand_eviction_chains(self):
        chains = defaultdict(int)
        seen = set()

        # all eviction chains start with the addr evicted by a tr
        for cand_addr in self.stat_cand_evicted_by_tr:
            l = 0
            while cand_addr in self.stat_cand_evict_cand_edges:
                seen.add(cand_addr)
                cand_addr_new = self.stat_cand_evict_cand_edges[cand_addr]
                if cand_addr_new in seen:
                    print(self.stat_cand_evicted_by_tr)
                    print(cand_addr, cand_addr_new)
                    print("Found addr conflicting with more than 1 TR!")
                    # TODO there is a bug here with inf loops?
                    break
                    #assert(0)
                cand_addr = cand_addr_new
                l += 1
            if l != 0:
                chains[l]+=1
        return chains

    def clear_eviction_chain_stats(self):
        self.stat_cand_evict_cand_edges.clear()
        self.stat_cand_evicted_by_tr.clear()

    def clear_all_stats(self):
        self.stat_cand_evict_cand_edges.clear()
        self.stat_num_tr_accesses = 0
        self.stat_num_prune_accesses = 0
        self.stat_num_check_accesses = 0
        self.stat_num_candidate_flushes = 0
        self.stat_num_tr_flushes = 0
        self.stat_num_misses = 0

    def get_accesses(self):
        return self.stat_num_tr_accesses, \
            self.stat_num_prune_accesses,\
            self.stat_num_check_accesses,\
            self.stat_num_candidate_flushes,\
            self.stat_num_misses

    ################ END STATS ###################

    def info(self):
        print("Basic set-associative cache with random replacement policy!")
        print("number of ways = ", self.num_ways,
                "; number of sets = ", self.num_sets)
        print("size = ", self.num_ways*self.num_sets*64*1.0/2**20, "MB")

    def get_tag(self, addr):
        return (addr>>self.block_bits)

    def get_set(self, addr):
        return (addr>>self.block_bits) % self.num_sets

    # If hit, return True and the cache location (true, way, set)
    # If miss, return False and the location can be inserted into
    def probe(self, addr):
        ## this is a simple set-associative cache
        set_index = self.get_set(addr)
        addr_tag = self.get_tag(addr)
        for i in range(self.num_ways):
            if self.tags[i, set_index] == addr_tag:
                return (True, (i, set_index))

        ## use random replacement policy
        for i in range(self.num_ways):
            if self.tags[i, set_index] == -1:
                return (False, (i, set_index))

        return(False, (randint(0,self.num_ways-1), set_index))

    def clear_log(self):
        self.log = []

    def print_log(self, output):
        for i in range(len(self.log)):
            way_id = self.log[i][0]
            set_index = self.log[i][1]
            old_addr = self.log[i][2]
            new_addr = self.log[i][3]
            if old_addr == new_addr:
                event = 'Hit'
            elif new_addr < 0:
                event = 'Flush'
            elif old_addr < 0:
                event = 'Insert'
            else:
                event = 'Conflict'
            print(hex(old_addr), "==>", hex(new_addr), "[%d,%d] " %
                    (way_id, set_index), event,
                    file=output)

    #----DEBUG USE ONLY----
    def check_duplication(self, addr):
        tag = self.get_tag(addr)
        for i in range(self.num_ways):
            for j in range(self.num_sets):
                if self.tags[i, j] == tag:
                    print(hex(addr), ' in  [',i,',',j,']')

    # To insert an address at a cache location
    def insert(self, addr, loc):
        way_id = loc[0]
        set_index = loc[1]
        addr_tag = self.get_tag(addr)

        ## STATS ##
        old_tag = self.tags[way_id, set_index]
        if old_tag == -1:
            old_addr = old_tag
        else:
            old_addr = old_tag<<self.block_bits  #TODO: this must make sure addree are all block aligned
        #self.track_cand_evictions(addr, old_addr)

        ## DEBUG ONLY -----
        if cache_debug == True:
            #print("Evict Event [way:", way_id, ", set", set_index, "] : ",
            #    hex(old_addr), " ==> ", hex(addr))
            self.log.append([loc[0], loc[1], old_addr, addr])
        ## DEBUG END ----

        self.tags[way_id, set_index] = addr_tag
        return old_addr

    def flush(self, addr):  #TODO flush cannot be used on skewed cache, it distroy LUR
        (hit, loc) = self.probe(addr)
        if hit == True:
            self.tags[loc[0], loc[1]] = -1
            if cache_debug == True:
                self.log.append([loc[0], loc[1], addr, -1])

    def access(self, addr, prune=True):
        (hit, loc) = self.probe(addr)
        old_addr = None
        if hit == False:
            self.stat_num_misses += 1
            old_addr = self.insert(addr, loc)

        if cache_debug == True and hit == True:
            self.log.append([loc[0], loc[1], addr, addr])

        if addr in self.stat_track_trs:
            self.stat_num_tr_accesses += 1
        else:
            if prune:
                self.stat_num_prune_accesses += 1
            else:
                self.stat_num_check_accesses += 1
        #self.track_cand_evictions(hit, addr, old_addr) #TODO add this
        return hit, old_addr

    '''
    def group_access(self, addrs, prune=True, rev=False):
        miss_addrs = []
        evicted_addrs = []
        addrs = sorted(list(addrs))
        num_addrs = len(addrs)
        for i in range(num_addrs):
            if rev:
                i = num_addrs - i - 1
            addr = addrs[i]
            hit, old_addr = self.access(addr)
            if hit==False:
                self.stat_num_misses += 1
                if True: #old_addr != -1: #For L1 become valid must tell L2
                    miss_addrs.append(addr)
                if old_addr != -1:
                    evicted_addrs.append(old_addr)

        if set(addrs).issubset(self.stat_track_trs):
            self.stat_num_tr_accesses += len(addrs)
        else:
            if prune:
                self.stat_num_prune_accesses += len(addrs)
            else:
                self.stat_num_check_accesses += len(addrs)

        self.track_cand_evictions(miss_addrs, evicted_addrs)
        
        return miss_addrs, evicted_addrs

    def group_access_stop_first_miss(self, addrs, rev=False):
        # we only call this on check if we're not greedy
        self.stat_num_check_accesses += len(addrs)
        addrs = sorted(list(addrs))
        num_addrs = len(addrs)
        for i in range(num_addrs):
            if rev:
                i = num_addrs - i - 1
            addr = addrs[i]
            hit,old_addr = self.access(addr)
            if hit==False:
                if old_addr != -1:
                    self.track_cand_evictions([addr], [old_addr])
                return [addr], [old_addr]
        return [],[]
    '''

    def group_flush(self, addrs):
        for addr in addrs:
            self.flush(addr)
        if set(addrs).issubset(self.stat_track_trs):
            self.stat_num_tr_flushes += len(addrs)
        else:
            self.stat_num_candidate_flushes += len(addrs)

class LRUCache(Cache):
    def __init__(self, num_ways, num_sets):
        super().__init__(num_ways, num_sets, num_ways)
        self.block_bits = 6 # assume the block size = 2**6
        self.num_ways = num_ways
        self.num_sets = num_sets
        #initialize all the addresses in the cache as -1
        self.tags = numpy.full((num_ways, num_sets), -1, dtype=int)
        self.LRUs = numpy.zeros((num_ways, num_sets), dtype=int)

    def info(self):
        print("Basic set-associative cache with pseudo LRU replacement policy!")
        print("number of ways = ", self.num_ways,
                "; number of sets = ", self.num_sets)
        print("size = ", self.num_ways*self.num_sets*64*1.0/2**20, "MB")

    def set_lru_bits(self, way_id, set_index):
        self.LRUs[way_id, set_index] = 1

        ## if all bits are 1, reset all to 0
        i = 0
        while i < self.num_ways:
            if self.LRUs[i, set_index] == 0:
                break
            i += 1

        if i == self.num_ways:
            # need to rest all LRU bits
            for j in range(self.num_ways):
                self.LRUs[j, set_index] = 0

    # If hit, return True and the cache location (true, way, set)
    # If miss, return False and the location can be inserted into
    def probe(self, addr):
        ## this is a simple set-associative cache
        set_index = self.get_set(addr)
        addr_tag = self.get_tag(addr)
        for i in range(self.num_ways):
            if self.tags[i, set_index] == addr_tag:
                self.set_lru_bits(i, set_index)
                return (True, (i, set_index))

        for i in range(self.num_ways):
            if self.tags[i, set_index] == -1:
                self.set_lru_bits(i, set_index)
                return (False, (i, set_index))

        for i in range(self.num_ways):
            if self.LRUs[i, set_index] == 0:
                self.set_lru_bits(i, set_index)
                return (False, (i, set_index))

        self.set_lru_bits(0, set_index)
        return(False, (0, set_index))
