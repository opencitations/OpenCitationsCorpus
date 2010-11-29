#!/usr/bin/env python
# -*- coding=utf-8 -*-
"""Fallback parser, used if no other better parser is found for a given Journal/article"""

from base import NotImplemented, PubMedParser, NoIDFound, flatten_element

import sys
from hashlib import md5
from itertools import chain

VERSION = 0.2
REPO = "http://bitbucket.org/beno/PubMed-OA-network-analysis-scripts"

class Flattening(PubMedParser):
  def plugin_warmup(self):
    """Doing module import here, to catch import errors for the manager"""
    
    self.name = "Flattening"
    self.actson = {'journals':{'_fallback':0.1}} # acts on all journals with weight 0
    self.version = VERSION
    self.repo = REPO

    return True

  def _comp_biblio(self, d, quiet=True):
    """Full bibliographic data, as far as that is possible for the article itself"""
    # setup the dict with blank values:
    anode = {'source':'', 'title':'', 'year':'', 'volume':''}
    atitle = d.xpath('/article/front/article-meta/title-group/article-title')
    if atitle:
      anode['title'] = flatten_element(atitle[0])
    
    pubdate = list(chain(d.xpath("/article/front/article-meta/pub-date[@pub-type='ppub']"),
                         d.xpath("/article/front/article-meta/pub-date[@pub-type='epub']")))
    if pubdate:
        for e in pubdate[0].xpath('year|month|day'):
            anode[e.tag] = e.text


    av = d.xpath('/article/front/article-meta/volume')
    if av:
      # grab the first one
      anode['volume'] = av[0].text
    av = d.xpath('/article/front/article-meta/issue')
    if av:
      # grab the first one
      anode['issue'] = av[0].text
    return anode

  def _comp_citations(self, d, quiet=True):
    """List of citations for a given article. Returns a dict, with citations from
     the 'citation', 'element-citation' and 'mixed-citation' elements."""
    def get_citations(cite_list, type_attrib):
      citations_list = []
      for citation in cite_list:
        ctype = citation.get(type_attrib, '')
        if ctype.lower() == "journal":
          # get pmid or doi
          c_id = None
          for pub_id in citation.xpath("pub-id"):
            t = pub_id.get("pub-id-type")
            if not c_id:
              c_id = "%s:%s" % (t, pub_id.text)
            if t == "pmid":
              break
            elif t == "doi":
              c_id = "doi:%s" % pub_id.text
          if c_id == None:
            # PLoS sometimes hides it's DOIS in comment/ext-link
            doi_comment = citation.xpath("comment/ext-link")
            if len(doi_comment) == 1:
              c_id = "doi:%s" % doi_comment[0].text
                      
          node_p = {'title':'','source':'','year':'','volume':'','publisher-name':'', 'ctype':'journal'}
          title_n = citation.find("article-title")
          if title_n != None:
            # If there is italic or other formatting around the title:
            if title_n.getchildren():
              inner = title_n.getchildren()[0]
              node_p['title'] = u"<%s>%s</%s>" % (inner.tag, inner.text, inner.tag)
            else:
              node_p['title'] = title_n.text or ''

          for name in ('publisher-name', 'year', 'source', 'volume', 'issue'):
            node = citation.find(name)
            if node is not None:
              if len(node):
                node = node[0]
              if node.text:
                node_p[name] = node.text


          ## TODO - get author list if one exists
          if c_id == None:
            hash_string = node_p['title']+node_p['source']+node_p['year']+node_p['publisher-name']
            c_id = "j:"+md5(hash_string.encode("utf-8")).hexdigest()
          
          citations_list.append((c_id, node_p))
        elif ctype.lower() == "book":
          # erm... hash the title + year for an id of sorts?
          node_p = {'title':'','source':'','year':'','volume':'', 'ctype':'book'}
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
              
          ## TODO - get author list if one exists
          c_id = "b:"+md5(hash_string.encode("utf-8")).hexdigest()
          
          citations_list.append((c_id, node_p))
      return citations_list
      
    # 2 Get PMIDs/DOIs/Books cited
    overall_citations = {}
    cite_list = d.xpath('/article/back/ref-list/*/citation')
    type_attrib = 'citation-type'
    if len(cite_list) !=0:
      overall_citations['citation'] = get_citations(cite_list, type_attrib)
    cite_list = d.xpath('/article/back/ref-list/*/element-citation')
    type_attrib = 'publication-type'
    if len(cite_list) !=0:
      overall_citations['element-citation'] = get_citations(cite_list, type_attrib)
    cite_list = d.xpath('/article/back/ref-list/*/mixed-citation')
    type_attrib = 'publication-type'
    if len(cite_list) !=0:
      overall_citations['mixed-citation'] = get_citations(cite_list, type_attrib)
    return overall_citations

  def _comp_article_id(self, d, quiet=True):
    """Get the ID for a given article - in order of preference: PMID, PMD, DOI, other"""
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
          raise NoIDFound, "Cannot find an id from this item"
    if not quiet:
      print "Found id of %s for %s" % (a_id, path_to_nxml)
    return a_id

  def _comp_all_article_ids(self, d, quiet=True):
    """Get all the IDs for a given article."""
    ids = {}
    for id_element in d.xpath('/article/front/article-meta/article-id'):
      ids[id_element.get("pub-id-type")] = id_element.text
      if not quiet:
        print "Found id of %s:%s for %s" % (id_element.get("pub-id-type"), id_element.text, path_to_nxml)
    return ids
