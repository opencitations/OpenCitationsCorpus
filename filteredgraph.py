#!/usr/bin/env python

import networkx as nx

import os, sys

import re

# {cmd} journal regex 

assert len(sys.argv) == 3

_, journal, regex = sys.argv

assert os.path.isfile(journal+".yaml")

print "Compiling regex: %s" % regex
p = re.compile(regex, re.U)

print "Loading YAML network graph for %s" % journal
g = nx.read_yaml(journal+".yaml")

print "Creating a directional graph to hold just the citation chains"
filtered_g = nx.DiGraph()
filtered_g.level = {}
filtered_g.position = {}

print "Scanning nodes for title regex matches"
hits = set()
for node in g.nodes(data=True):
  if node[1].get('source', '') == journal:
    m = p.search(node[1].get('title','') or '')
    if m != None:
      hits.add(node[0])
      filtered_g.level[node[0]] = 1
      filtered_g.add_node(node[0], **node[1])

print "Seed IDs:"
print hits

def arrange_nodes_at_level(filtered_g, nodes, level):
  y = 900 - 100 * level
  dx = 800 / len(nodes)
  st_x = 0
  for node in nodes:
    filtered_g.position[node] = (st_x, y)
    st_x =st_x + dx

def get_children(g, nodes, filtered_g, level):
  children = {}
  # got seed ids
  for uid in hits:
    cites = g.successors(uid)
    if cites:
      for item in cites:
        if g.node[item].get('source','') == journal:
          if not children.has_key(uid):
            children[uid] = []
          children[uid].append(item)
          filtered_g.add_node(item, **g.node[item])
          filtered_g.add_edge(uid, item)
          filtered_g.level[item] = level+1
  print children
  return children

arrange_nodes_at_level(filtered_g, hits, 0)

level = 1
while(hits):
  print "Getting cited works at level %s" % level
  children_dict = get_children(g, hits, filtered_g, level)
  hits = set()
  if children_dict:
    for l in children_dict.values():
      hits.update(l)
    print "Found %s cited works within %s by %s articles at level %s" % (len(hits), journal, len(children_dict.keys()), level)
    arrange_nodes_at_level(filtered_g, hits, level)
    level = level + 1

print "Writing out YAML graph to %s" % (journal+"-"+regex+".yaml")
nx.write_yaml(filtered_g, journal+"-"+regex+".yaml")

print "Attempting to draw graph for viewing"
import matplotlib.pyplot as plt
plt.figure(figsize=(8,8))
#nx.draw(filtered_g, node_colors=[float(filtered_g.level[x] % 4 *64) for x in filtered_g])
nx.draw(filtered_g, filtered_g.position)
print "Saving graph image as %s" % (journal+"-"+regex+".png")
plt.savefig(journal+"-"+regex+".png")
plt.show()
