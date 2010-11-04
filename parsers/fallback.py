#!/usr/bin/env python
# -*- coding=utf-8 -*-
"""Fallback parser, used if no other better parser is found for a given Journal/article"""

from base import NotImplemented, PubMedParser, NoIDFound

from inspect import getdoc  # to get component docs automatically

from hashlib import md5

VERSION = 0.2
REPO = "http://bitbucket.org/beno/PubMed-OA-network-analysis-scripts"
COMP_PREF = "_comp_"

class Fallback(PubMedParser):
  def __init__(self):  # Use conf files for per instance settings.
    self.name = "Fallback"
    self.actson = {'journals':{'*':100}} # acts on all journals with weight 100

    self.provides = {}  # Automagic setting of components
    
    all_comps = [c[len(COMP_PREF):] for c in dir(self) if c.startswith(COMP_PREF)]
    for comp in all_comps:
      comment = getdoc(getattr(self, "%s%s" % (COMP_PREF, comp)))
      if not comment:
        comment = "No documentation available"
      self.provides[comp] = comment

    self.version = VERSION 
    self.repo = REPO

  def _comp_biblio(self, d, quiet=True):
    """Full bibliographic data, as far as that is possible for the article itself"""
    # setup the dict with blank values:
    anode = {'source':'', 'title':'', 'year':'', 'volume':''}
    atitle = d.xpath('/article/front/article-meta/title-group/article-title')
    if atitle:
      # If there is italic or other formatting around the title:
      if atitle[0].getchildren():
        atitle = u"<%s>%s</%s>" % (atitle[0].tag, atitle[0].text, atitle[0].tag)
      else:
        atitle = atitle[0].text
    ayear = d.xpath('/article/front/article-meta/pub-date/year')
    if ayear:
      # grab the first one
      anode['year'] = ayear[0].text
    av = d.xpath('/article/front/article-meta/volume')
    if av:
      # grab the first one
      anode['volume'] = av[0].text
    return anode

  def _comp_citations(self, d, quiet=True):
    """List of citations for a given article. Returns a dict, with citations from
     the 'citation', 'element-citation' and 'mixed-citation' elements."""
    def get_citations(cite_list, type_attrib):
      citations_list = []
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
                      
          node_p = {'title':'','source':'','year':'','volume':'','publisher-name':''}
          source_n = citation.find("source")
          if source_n != None:
            if source_n.getchildren():
              source_n = source_n.getchildren()[0]
            if source_n.text:
              node_p['source'] = source_n.text
          else:
            title_n = citation.find("article-title")
            if title_n != None:
              # If there is italic or other formatting around the title:
              if title_n.getchildren():
                node_p['title'] = u"<%s>%s</%s>" % (title_n.tag, title_n.text, title_n.tag)
              else:
                node_p['title'] = title_n.text
          pubname_n = citation.find("publisher-name")
          if pubname_n !=None:
            if pubname_n.getchildren():
              pubname_n = pubname_n.getchildren()[0]
            if pubname_n.text:
              node_p['publisher-name'] = pubname_n.text
          year_n = citation.find("year")
          if year_n != None:
            if year_n.getchildren():
              year_n = year_n.getchildren()[0]
            if year_n.text:
              node_p['year'] = year_n.text  
          ## TODO - get author list if one exists
          if c_id == None:
            hash_string = node_p['title']+node_p['source']+node_p['year']+node_p['publisher-name']
            c_id = "j:"+md5(hash_string.encode("utf-8")).hexdigest()
          
          citations_list.append((c_id, node_p))
        elif ctype.lower() == "book":
          # erm... hash the title + year for an id of sorts?
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

  def gather_data(self, path_to_nxml, gather=['article_id','authors','citations','biblio'], quiet=True):
    if not quiet:
      print "%s - tackling %s. Attempting to extract %s" % (self.name, path_to_nxml, gather) 
      print "Opening %s with lxml.etree" % (path_to_nxml)
    d = self.ET.parse(path_to_nxml)
    data_pkg = {'parser_name':self.name, 'repo':self.repo, 'version':str(self.version)}
    for component in gather:
      if hasattr(self, "%s%s" % (COMP_PREF, component)):
        data_pkg[component] = getattr(self, "_comp_%s" % component)(d, quiet=quiet)
    return data_pkg

  def plugin_warmup(self):
    """Doing module import here, to catch import errors for the manager"""
    from lxml import etree as ET
    self.ET = ET
    return True
