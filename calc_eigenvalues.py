#!/usr/bin/env python

import networkx as nx
try:
    import numpy.linalg
    eigenvalues=numpy.linalg.eigvals
except ImportError:
    raise ImportError("numpy can not be imported.")

import matplotlib.pyplot as plt

try:
    from pylab import *
except:
    pass

from graphml import read_graphml

import sys,os

if len(sys.argv)==2:
  fn = sys.argv[1]
  print "Reading in %s" % fn
  g = read_graphml(fn)
  print "Generating a generalized laplacian"
  l = nx.generalized_laplacian(g)
  print "Calculating eigenvalues"
  e=eigenvalues(l)
  print("Largest eigenvalue:", max(e))
  print("Smallest eigenvalue:", min(e))
  # plot with matplotlib if we have it
  # shows "semicircle" distribution of eigenvalues
  try:
    print "Trying to plot semicircle of eigenvalues"
    hist(e,bins=100) # histogram with 100 bins
    xlim(0,2)  # eigenvalues between 0 and 2
    show()
    #plt.savefig("%s.eigen.png" % fn)
  except:
    pass


