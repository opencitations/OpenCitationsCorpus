#!/usr/bin/env python
# -*- coding=utf-8 -*-
"""Fallback parser, used if no other better parser is found for a given Journal/article"""

from base import NotImplemented, PubMedParser

VERSION = 0.1
REPO = "http://bitbucket.org/beno/PubMed-OA-network-analysis-scripts"


class Fallback(PubMedParser):
  def __init__(self):  # Use conf files for per instance settings.
    self.name = "Name for the parser, typically the filename"
    self.actson = {'journals':{'*':100}} # acts on all journals with weight 100
    self.provides = {'authors':'author list, if it exists',
                     'citations':'List of citation information in the order it occurs. Returns source, title, author list, date if found',
                     'full_biblio':'full bibliographic data, as far as that is possible for the article itself'}
    self.version = VERSION 
    self.repo = REPO

  def _gather_full_biblio(self, d):
    # setup the dict with blank values:
    anode = {'source':'', 'title':'', 'year':'', 'volume':''}
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
    

  def gather_data(self, path_to_nxml, gather=['authors','citations','full_biblio'], quiet=True):
    if not quiet:
      print "%s - tackling %s. Attempting to extract %s" % (self.name, path_to_nxml, gather) 
      print "Opening %s with lxml.etree" % (path_to_nxml)
    d = ET.parse(path_to_nxml)
    # 1 Get PMID (from /article/front/article-meta/article-id[@pub-id-type="pmid"])
    id_list = d.xpath('/article/front/article-meta/article-id[@pub-id-type="pmid"]')
    if len(id_list) >= 1:
      a_id = "pmid:%s" % (id_list[0].text)
    else:
      # hmm no pmid - doi as fallback?
      id_list = d.xpath('/article/front/article-meta/article-id[@pub-id-type="doi"]')
      if len(id_list) >= 1:
        # Found at least one doi
        a_id = "doi:%s" % (id_list[0].text)
      else:
        id_list = d.xpath('/article/front/article-meta/article-id')
        if len(id_list) >= 1:
          a_id = "%s:%s" % (id_list[0].get("pub-id-type"), id_list[0].text)
        else:
          raise FailedParse, "Cannot find an id from this item"

    if not quiet:
      print "Found id of %s for %s" % (a_id, path_to_nxml)
    
    g.add_node(pmid, **anode)

  def plugin_warmup(self):
    """Doing module import here, to catch import errors for the manager"""
    from lxml import etree as ET # this varient provides good, fast xpath support which is required.
    return True

PUBMED_PLUGINS.register(PubMedParser())
