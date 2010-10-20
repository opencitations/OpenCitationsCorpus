#!/usr/bin/env python
# -*- coding=utf-8 -*-

import networkx as nx
import matplotlib.pyplot as plt

from hashlib import md5

# use the lxml implementation of etree for xpath support
from lxml import etree as ET

import os, sys

from graphml import write_graphml

if len(sys.argv) == 2 and os.path.isdir(sys.argv[1]): # assume journal is passed on the commandline
  jlist = [sys.argv[1]]
else:
  jlist = [x for x in os.listdir(".") if os.path.isdir(x)]

def generate_network(journal_dir):
  g = nx.DiGraph()
  for nlmxml in [x for x in os.listdir(journal_dir) if x.endswith("nxml")]:
    print "Processing %s in %s" % (nlmxml, journal_dir)
    d = ET.parse(os.path.join(journal_dir, nlmxml))
    # 1 Get PMID (from /article/front/article-meta/article-id[@pub-id-type="pmid"])
    id_list = d.xpath('/article/front/article-meta/article-id[@pub-id-type="pmid"]')
    if not len(id_list) == 1:
      # hmm no pmid - doi as fallback
      id_list = d.xpath('/article/front/article-meta/article-id[@pub-id-type="doi"]')
      if not len(id_list) == 1:
        id_list = d.xpath('/article/front/article-meta/article-id')
        pmid = "%s:%s" % (id_list[0].get("pub-id-type"), id_list[0].text)
      else:
        pmid = "doi:%s" % (id_list[0].text)
    else:
      pmid = id_list[0].text
    # Get some metadata about article if node doesn't exist
    if not g.has_node(pmid):
      # year + title to start
      anode = {'source':journal_dir, 'title':'', 'year':'', 'volume':''}
      atitle = d.xpath('/article/front/article-meta/title-group/article-title')
      if atitle:
        #should only be one
        if atitle[0].getchildren():
          atitle = atitle[0].getchildren()
        if atitle[0].text:
          anode['title'] = atitle[0].text
      ayear = d.xpath('/article/front/article-meta/pub-date/year')
      if ayear:
        # grab the first one
        anode['year'] = ayear[0].text
      av = d.xpath('/article/front/article-meta/volume')
      if av:
        # grab the first one
        anode['volume'] = av[0].text
      g.add_node(pmid, **anode)
    
    def graph_citations(g, cite_list, type_attrib):
      for citation in cite_list:
        ctype = citation.get(type_attrib)
        if ctype.lower() == "journal":
          # get pmid or doi
          c_id = None
          for pub_id in citation.xpath("pub-id"):
            t = pub_id.get("pub-id-type")
            if not c_id:
              c_id = "%s:%s" % (t, pub_id.text)
	    if t == "pmid":
	      c_id = pub_id.text
              break
            elif t == "doi":
              c_id = "doi:%s" % pub_id.text
          if c_id == None:
            # PLoS sometimes hides it's DOIS in comment/ext-link
            doi_comment = citation.xpath("comment/ext-link")
            if len(doi_comment) == 1:
              c_id = "doi:%s" % doi_comment[0].text
          if c_id == None:
            node_p = {'title':'','source':'','year':'','volume':''}
            hash_string = ""
            title_n = citation.find("source")
            if title_n != None:
              if title_n.getchildren():
                title_n = title_n.getchildren()[0]
              if title_n.text:
                node_p['title'] = title_n.text
                hash_string = hash_string + title_n.text
            else:
              title_n = citation.find("article-title")
              if title_n != None:
                if title_n.getchildren():
                  title_n = title_n.getchildren()[0]
                if title_n.text:
                  node_p['title'] = title_n.text
                  hash_string = hash_string + title_n.text
            source_n = citation.find("publisher-name")
            if source_n !=None:
              if source_n.getchildren():
                source_n = source_n.getchildren()[0]
              if source_n.text:
                node_p['source'] = source_n.text
                hash_string = hash_string + source_n.text
            year_n = citation.find("year")
            if year_n != None:
              if year_n.getchildren():
                year_n = year_n.getchildren()[0]
              if year_n.text:
                node_p['year'] = year_n.text
                hash_string = hash_string + year_n.text
            c_id = "j:"+md5(hash_string.encode("utf-8")).hexdigest()
          # Get some metadata about article if node doesn't exist
          if not g.has_node(c_id):
            node_p = {'title':'','source':'','year':'','volume':''}
            title_n = citation.find("article-title")
            if title_n != None:
              if title_n.getchildren():
                title_n = title_n.getchildren()[0]
              if title_n.text:
                node_p['title'] = title_n.text
            source_n = citation.find("source")
            if source_n != None:
              if source_n.getchildren():
                source_n = source_n.getchildren()[0]
              if source_n.text:
                node_p['source'] = source_n.text
            year_n = citation.find("year")
            if year_n != None and year_n.text:
              node_p['year'] = year_n.text
            volume_n = citation.find("volume")
            if volume_n != None and volume_n.text:
              node_p['volume'] = volume_n.text
            g.add_node(c_id, **node_p)
          # add directed edge for this
          g.add_edge(pmid, c_id)
        elif ctype.lower() == "book":
          # erm... hash the title + year for an id?
          node_p = {'title':'','source':'','year':'','volume':''}
          hash_string = ""
          title_n = citation.find("source")
          if title_n != None:
            if title_n.getchildren():
              title_n = title_n.getchildren()[0]
            if title_n.text:
              node_p['title'] = title_n.text
              hash_string = hash_string + title_n.text
          else:
            title_n = citation.find("article-title")
            if title_n != None:
              if title_n.getchildren():
                title_n = title_n.getchildren()[0]
              if title_n.text:
                node_p['title'] = title_n.text
                hash_string = hash_string + title_n.text
          source_n = citation.find("publisher-name")
          if source_n !=None:
            if source_n.getchildren():
              source_n = source_n.getchildren()[0]
            if source_n.text:
              node_p['source'] = source_n.text
              hash_string = hash_string + source_n.text
          year_n = citation.find("year")
          if year_n != None:
            if year_n.getchildren():
              year_n = year_n.getchildren()[0]
            if year_n.text:
              node_p['year'] = year_n.text
              hash_string = hash_string + year_n.text
          c_id = "b:"+md5(hash_string.encode("utf-8")).hexdigest()
          if not g.has_node(c_id):
            g.add_node(c_id, **node_p)
          # add directed edge for this
          g.add_edge(pmid, c_id)

    # 2 Get PMIDs/DOIs/Books cited
    cite_list = d.xpath('/article/back/ref-list/*/citation')
    type_attrib = 'citation-type'
    if len(cite_list) !=0:
      graph_citations(g, cite_list, type_attrib)
    cite_list = d.xpath('/article/back/ref-list/*/element-citation')
    type_attrib = 'publication-type'
    if len(cite_list) !=0:
      graph_citations(g, cite_list, type_attrib)
    cite_list = d.xpath('/article/back/ref-list/*/mixed-citation')
    type_attrib = 'publication-type'
    if len(cite_list) !=0:
      graph_citations(g, cite_list, type_attrib)
  return g

errorlist = open("unparsable.log", "w")

for journal in jlist:
  if os.path.exists(journal+".yaml"):
    print "Not getting %s" % journal
    #continue
  try:
    g = generate_network(journal)
    #print "Saving as YAML - %s" % (journal+".yaml")
    #nx.write_yaml(g, journal+".yaml")
    print "Saving as New shiny GraphML - %s" % (journal+".gml")
    write_graphml(g, open(journal+".gml", "w"))
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

