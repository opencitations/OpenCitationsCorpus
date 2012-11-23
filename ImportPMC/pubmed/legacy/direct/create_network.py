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
                 'author':'',
                 'editor':'',
                 'nlmxml':''}
  for key in data_params:
    if key == "people":
      for group in data_params[key]:
        if group in node_params:
          node_params[group] = ";".join(data_params[key][group])
    elif key == "contributors":
      # reorient around the type
      dts = {}
      for contributor in data_params['contributors']:
        if not dts.has_key(contributor['type']):
          dts[contributor['type']] = []
        if contributor.has_key('surname') and contributor.has_key('given-names'):
          dts[contributor['type']].append(u"%s, %s" % (contributor['surname'], contributor['given-names']))
        elif contributor.has_key('surname'):
          dts[contributor['type']].append(contributor['surname'])
      for key in dts:
        if key in node_params:
          node_params[key] = u";".join(dts[key])
    elif key in node_params:
      node_params[key] = data_params[key]
    if key in additional:
      node_params[key] = additional[key]
  return node_params

def generate_network(journal_dir):
  g = nx.DiGraph()
  no_attribs = nx.DiGraph()
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
      no_attribs.add_node(nodeid)

    for ctype in info['citations'].keys():
      for c_id, citation_params in info['citations'][ctype]:
        if not g.has_node(c_id):
          citation_params['_xml_container'] = ctype
          g.add_node(c_id, **to_node_params(citation_params))
          no_attribs.add_node(c_id)
        # add directed edge for this
        g.add_edge(nodeid, c_id)
        no_attribs.add_edge(nodeid, c_id)
  return g, no_attribs

errorlist = open("unparsable.log", "w")
if __name__ == "__main__":
  for journal in jlist:
    try:
      g, no_attribs = generate_network(journal)
      filename = re.sub('[^a-z.]+', '-', journal.lower()).strip('-') + '.graphml'
      n_filename = re.sub('[^a-z.]+', '-', journal.lower()).strip('-') + '-nodesonly.graphml'
      print "Saving fully attrib'd graph as %s" % (filename)
      write_graphml(g, open(filename, "w"))
      print "Saving plain graph, no attributes as %s" % (n_filename)
      write_graphml(no_attribs, open(n_filename, "w"))
    except IndexError:
      print "ERROR Couldn't parse journal: %s" % journal
      errorlist.write("%s\n" % journal)

