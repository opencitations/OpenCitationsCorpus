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
  print "Drawing a simple graph"
  plt.figure(figsize=(15,15))
  nx.draw_circular(g)
  plt.savefig("%s.spectral.png" % fn) # save as png
  plt.show() # display
