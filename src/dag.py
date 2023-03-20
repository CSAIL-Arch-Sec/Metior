import json
from platform import node

def dag_to_dict(dagName):

    with open(dagName, mode='r') as f:
        data = json.load(f)
    
    nodeDict = dict()

    for node in data["node"]:
        if node["type"] == "G": continue

        time = node["absTime"]
        addr = node["address"]

        assert(str(time) not in nodeDict.keys())
        
        nodeDict[time] = addr

    return nodeDict

def unique_addr(nodeDict):
    unique = set()

    for x in nodeDict.values():
        unique.add(x >> 6)

    return len(unique)
