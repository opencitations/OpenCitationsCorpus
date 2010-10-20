#!/usr/bin/env python

try:
    import matplotlib.pyplot as plt
except:
    raise

import networkx as nx


import sys,os

if len(sys.argv)==2:
  fn = sys.argv[1]
  print "Reading in %s" % fn
  g = nx.read_yaml(fn)
  print "Simulating spring network..."
  pos=nx.spring_layout(g,iterations=100)
  plt.clf()
  print "Drawing a simple graph"
  plt.figure(figsize=(30,30))
  nx.draw(g,pos,node_size=20,with_labels=False)
  plt.savefig("%s.spring_no_label.png" % fn) # save as png
  #plt.show() # display
