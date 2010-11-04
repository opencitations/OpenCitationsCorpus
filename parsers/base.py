#!/usr/bin/env python
# -*- coding=utf-8 -*-

"""Base class for the exceptional parsers - exceptional in that they should
deal with exceptional content, rather than being exceptional in handling all
the content types"""

class NotImplemented(Exception):
  pass
class NoIDFound(Exception):
  pass

registry = []

COMP_PREF = "_comp_"

from lxml import etree as ET

from inspect import getdoc  # to get component docs automatically

class PubMedParser(object):
  class __metaclass__(type):
    def __init__(cls, name, bases, dict):
      super(type, cls).__init__()
      registry.append((name, cls))

  def __init__(self):  # Use conf files for per instance settings.
    """ Requires some registation attributes to be set up:
         self.name = "Name for the parser, typically the filename"
         self.actson = {key:value, ...}
           - currently, only 'journals':{'journal_name':weight, etc} supported
         self.provides = Dict of extracted packets with commments on what it does
                    eg {'authors':'author list, if it exists',
                        'citations':'List of citation information',
                        'full_biblio':'full bibliographic data, as far as that is possible'}
         self.version = Parser version (used to record provenance)
         self.repo = Repo location of parser (also a provenance item)
    """
    self.provides = {}  # Automagic setting of components
    
    all_comps = [c[len(COMP_PREF):] for c in dir(self) if c.startswith(COMP_PREF)]
    for comp in all_comps:
      comment = getdoc(getattr(self, "%s%s" % (COMP_PREF, comp)))
      if not comment:
        comment = "No documentation available"
      self.provides[comp] = comment

    self.name = "BaseParserPlugin"

  def gather_data(self, path_to_nxml, gather=['article_id','authors','citations','biblio'], quiet=True):
    if not quiet:
      print "%s - tackling %s. Attempting to extract %s" % (self.name, path_to_nxml, gather) 
      print "Opening %s with lxml.etree" % (path_to_nxml)
    d = ET.parse(path_to_nxml)
    data_pkg = {'parser_name':self.name, 'repo':self.repo, 'version':str(self.version)}
    for component in gather:
      if hasattr(self, "%s%s" % (COMP_PREF, component)):
        data_pkg[component] = getattr(self, "_comp_%s" % component)(d, quiet=quiet)
    return data_pkg

  def plugin_warmup(self):
    """ Do any per-instance initialisation here. Mainly used to see if the plugin is ready or workable.
        Throwing a NotImplemented error, or any other Exception will result in this plugin not being considered
        by the plugin manager.

        Any other return will cause the manager to think that this plugin is ready.

        PUBMED_PLUGINS.status("plugin name") will pass back the error thrown or True if the plugin is ready.
    """
    raise NotImplemented

  def __repr__(self):
    if hasattr(self, "name"):
      if hasattr(self, "version"):
        return "PubMed Parser plugin: '%s-v%s'" % (self.name, self.version)
      return "PubMed Parser plugin '%s'" % self.name
    else:
      return "Unnamed PubMed Parser"
