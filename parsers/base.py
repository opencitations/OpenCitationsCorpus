#!/usr/bin/env python
# -*- coding=utf-8 -*-

"""Base class for the exceptional parsers - exceptional in that they should
deal with exceptional content, rather than being exceptional in handling all
the content types"""

class NotImplemented(Exception):
  pass

class PubMedParser(object):
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
    raise NotImplemented

  def gather_data(self, path_to_nxml, gather=['authors','citations','full_biblio']):
    """Main function called to extract metadata from the passed nxml file at the given filepath"""
    # return {'authors':...., 'citations':...., etc}
    raise NotImplemented

  def plugin_warmup(self):
    """ Do any per-instance initialisation here. Mainly used to see if the plugin is ready or workable.
        Throwing a NotImplemented error, or any other Exception will result in this plugin not being considered
        by the plugin manager.

        Any other return will cause the manager to think that this plugin is ready.

        PUBMED_PLUGINS.status("plugin name") will pass back the error thrown or True if the plugin is ready.
    """
    raise NotImplemented

PUBMED_PLUGINS.register(PubMedParser())
