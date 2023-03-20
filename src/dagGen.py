def getPara(numPhase, numPara, latency, increment, nodeLatency, numTimingLayers, latencyArr = None):
  node = []
  edge = []

  # start node
  node.append({"nodeID": 0, "nodeType": "timing", "nodeLat": nodeLatency})
  for timingLayer in range(numTimingLayers):
    # main node
    for phaseID in range(numPhase):
      for paraID in range(numPara):
        nodeID = phaseID*numPara + paraID + 1 + (timingLayer * numPhase * numPara) + timingLayer
        node.append({"nodeID": nodeID, "nodeType": "memory", "cacheHit": 0})
    # end node
    node.append({"nodeID": (timingLayer+1)*numPhase*numPara+1+timingLayer, "nodeType": "timing", "nodeLat": nodeLatency})


  # start edge
  for timingLayer in range(numTimingLayers):
    for paraID in range(numPara):
      edge.append({"sourceID": (timingLayer*numPhase*numPara)+timingLayer, "destID": (timingLayer*numPhase*numPara)+(paraID+1) \
        + timingLayer, "latency": latency + increment*paraID})
    # main edge
    for phaseID in range(numPhase-1):
      if latencyArr != None:
        edgeLatency = latencyArr[(phaseID) % len(latencyArr)]
      else:
        edgeLatency = latency

      for paraID in range(numPara):
        nodeID0 = phaseID*numPara + paraID + 1 + (timingLayer*numPhase*numPara) + timingLayer
        nodeID1 = (phaseID+1)*numPara + paraID + 1 + (timingLayer*numPhase*numPara) + timingLayer
        edge.append({"sourceID": nodeID0, "destID": nodeID1, "latency": edgeLatency})
    # end edge
    for paraID in range(numPara):
      edge.append({"sourceID": (timingLayer+1)*numPhase*numPara-paraID+timingLayer, \
        "destID": (timingLayer+1)*numPhase*numPara+1+timingLayer, "latency": 0})

  return {"0":{"loop": 1, "node": node, "edge": edge}}

def getLayeredPara(numPhase, numPara, latency, increment, nodeLatency, latencyArr = None):
  node = []
  edge = []

  # start node
  node.append({"nodeID": 0, "nodeType": "timing", "nodeLat": nodeLatency})
  for timingLayer in range(numPhase):
    for paraID in range(numPara):
      nodeID = paraID + 1 + (timingLayer*(numPara+1))
      node.append({"nodeID": nodeID, "nodeType": "memory", "cacheHit": 0})
    # end node
    if timingLayer != numPhase -1:
      node.append({"nodeID": (timingLayer+1)*(numPara+1), "nodeType": "memory", "cacheHit": 1})
    else:
      node.append({"nodeID": (timingLayer+1)*(numPara+1), "nodeType": "timing", "cacheHit": 0})

  # start edge
  for timingLayer in range(numPhase):
    if latencyArr != None:
        edgeLatency = latencyArr[(timingLayer) % len(latencyArr)]
    else:
        edgeLatency = latency

    for paraID in range(numPara):
      edge.append({"sourceID": timingLayer*(numPara+1), "destID": paraID + 1 + (timingLayer*(numPara+1)), "latency": edgeLatency})
      edge.append({"sourceID": paraID + 1 + (timingLayer*(numPara+1)), "destID": (timingLayer+1)*(numPara+1), "latency": 1})


  return {"0":{"loop": 1, "node": node, "edge": edge}}

def getFullConnect(numPhase, numPara, latency, increment, nodeLatency, numTimingLayers):
  node = []
  edge = []

  # start node
  node.append({"nodeID": 0, "nodeType": "timing", "nodeLat": nodeLatency})
  for timingLayer in range(numTimingLayers):
    # main node
    for phaseID in range(numPhase):
      for paraID in range(numPara):
        nodeID = phaseID*numPara + paraID + 1 + (timingLayer * numPhase * numPara) + timingLayer
        node.append({"nodeID": nodeID, "nodeType": "memory"})
    # end node
    node.append({"nodeID": (timingLayer+1)*numPhase*numPara+1+timingLayer, "nodeType": "timing", "nodeLat": nodeLatency})

  for timingLayer in range(numTimingLayers):
    # start edge
    for paraID in range(numPara):
      edge.append({"sourceID": timingLayer*numPhase*numPara + timingLayer, \
          "destID": (timingLayer*numPhase*numPara) + paraID + 1 + timingLayer, "latency": latency + increment*paraID})

    # main edge
    for phaseID in range(numPhase-1):
      for paraID0 in range(numPara):
        for paraID1 in range(numPara):
          nodeID0 = phaseID*numPara + paraID0 + 1 + (timingLayer * numPhase * numPara) + timingLayer
          nodeID1 = (phaseID+1)*numPara + paraID1 + 1 + (timingLayer * numPhase * numPara) + timingLayer
          edge.append({"sourceID": nodeID0, "destID": nodeID1, "latency": latency})
    # end edge
    for paraID in range(numPara):
      edge.append({"sourceID": (timingLayer+1)*numPhase*numPara-paraID+timingLayer, \
        "destID": (timingLayer+1)*numPhase*numPara+1+timingLayer, "latency": latency})

  return {"0":{"loop": 1, "node": node, "edge": edge}}

def getSimple(numAcc, latency):
  node = []
  edge = []

  # start node
  for i in range(numAcc):  
      node.append({"nodeID": i, "nodeType": "memory"})
      if i > 0:
          edge.append({"sourceID": i-1, "destID": i, "latency": latency})

  return {"0":{"loop": 1, "node": node, "edge": edge}}

def getSimplePara(numAcc, gap):
  node = []
  edge = []

  node.append({"nodeID": 0, "nodeType": "timing", "nodeLat": 0})
    
  # start node
  for i in range(1, numAcc+1):  
      node.append({"nodeID": i, "nodeType": "memory"})
      edge.append({"sourceID": 0, "destID": i, "latency": i * gap})

  return {"0":{"loop": 1, "node": node, "edge": edge}}