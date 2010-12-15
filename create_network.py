#!/usr/bin/env python
# -*- coding=utf-8 -*-

from plugin_manager import Plugin_manager

P = Plugin_manager()

import networkx as nx
import matplotlib.pyplot as plt

from hashlib import md5

import os, sys, re

from graphml import write_graphml

if len(sys.argv) == 2 and os.path.isdir(sys.argv[1]): # assume journal is passed on the commandline
  jlist = [sys.argv[1]]
else:
  jlist = [x for x in os.listdir(".") if os.path.isdir(x)]

def to_node_params(data_params, **additional):
  # Graphml requires each node to have the same fields
  node_params = {'title':'',
                 'volume':'',
                 'issue':'',
                 'year':'',
                 'month':'',
                 '_xml_container':'',
                 'publisher-name':'',
                 'source':'',
                 'ctype':'',
                 'nlmxml':''}
  for key in node_params:
    if key in data_params:
      node_params[key] = data_params[key]
    if key in additional:
      node_params[key] = additional[key]
  return node_params

def generate_network(journal_dir):
  g = nx.DiGraph()
  for nlmxml in [x for x in os.listdir(journal_dir) if x.endswith("nxml")]:
    print "Processing %s in %s" % (nlmxml, journal_dir)
    info = P.handle(journal_dir, os.path.join(journal_dir, nlmxml), components=["article_id", "all_article_ids", "biblio", "citations"])
    
    nodeid = info['article_id']
    if not g.has_node(nodeid):
      info['biblio']['source'] = u" ".join(journal_dir.split("_"))
      g.add_node(nodeid, **to_node_params(info['biblio'],
                                          source=u" ".join(journal_dir.split("_")),
                                          nlmxml=os.path.join(journal_dir, nlmxml) )
                                          )

    for ctype in info['citations'].keys():
      for c_id, citation_params in info['citations'][ctype]:
        if not g.has_node(c_id):
          citation_params['_xml_container'] = ctype
          g.add_node(c_id, **to_node_params(citation_params))
        # add directed edge for this
        g.add_edge(nodeid, c_id)
  return g

errorlist = open("unparsable.log", "w")
if __name__ == "__main__":
  for journal in jlist:
    try:
      g = generate_network(journal)
      filename = re.sub('[^a-z.]+', '-', journal.lower()).strip('-') + '.graphml'
      #print "Saving as YAML - %s" % (journal+".yaml")
      #nx.write_yaml(g, journal+".yaml")
      print "Saving as New shiny GraphML - %s" % (filename)
      write_graphml(g, open(filename, "w"))
      #print "Saving as GraphML - %s" % (journal+".gml")
      #nx.write_graphml(g, journal+".gml")
    except IndexError:
      print "ERROR Couldn't parse journal: %s" % journal
      errorlist.write("%s\n" % journal)
  # nx.draw()

  #print "Saving as graphviz dot file - %s" % (journal+".dot")
  #nx.write_dot(g, journal+".dot")
  #print "Calculating eigenvalues"
  #L=nx.generalized_laplacian(g)
  #e=nx.eigenvalues(L)
  #print("Largest eigenvalue:", max(e))
  #print("Smallest eigenvalue:", min(e))
  # plot with matplotlib if we have it
  # shows "semicircle" distribution of eigenvalues
  #try:
  #  nx.hist(e,bins=100) # histogram with 100 bins
  #  nx.xlim(0,2)  # eigenvalues between 0 and 2
  #  nx.show()
  #except:
  #  pass

  #print "Saving %s w/ GraphViz" % (journal+".dot")
  #nx.draw_graphviz(g)
  #nx.write_dot(journal+".dot")
  #print "pylab drawings:"
  #print "Circular %s"  % (journal+"circ.png")
  #nx.draw_circular(g)
  #plt.savefig(journal+"circ.png")

