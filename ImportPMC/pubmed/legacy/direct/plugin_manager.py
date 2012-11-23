#!/usr/bin/env python
# -*- coding=utf-8 -*-

from parsers import *
from operator import itemgetter

class NoValidPlugin(Exception):
  pass

class Plugin_manager(object):
  def __init__(self):
    self.plugins = {}
    self.journal_w = {}
    self.status = {}
    self._register_plugins()

  def _register_plugins(self):
    for plugin, cls in registry:
      self._register(cls())

  def _register(self, plugin_instance):
    try:
      plugin_instance.plugin_warmup()
      assert plugin_instance.name != None
      assert isinstance(plugin_instance.actson, dict)
      assert isinstance(plugin_instance.provides, dict)
      assert plugin_instance.version != None
      assert plugin_instance.repo != None
      assert plugin_instance.actson.has_key('journals')    
      print "Registering %s" % plugin_instance
    except AssertionError:
      print "Plugin '%s' failed to provide base attributes about itself" % repr(plugin_instance)
      return
    except Exception, e:
      if self.plugins.has_key(plugin_instance.name):
        print "Plugin failed to initialise - %s and name is already registered: %s" % plugin_instance.name
      else:
        print "Plugin %s failed to initialise" % plugin_instance.name
        self.status[plugin_instance.name] = e
      return
    if self.plugins.has_key(plugin_instance.name):
      print "Name collision: %s is already registered as a plugin" % plugin_instance.name
    else:
      """Register plugin and add the weighting to journal_w"""
      self.plugins[plugin_instance.name] = plugin_instance
      for key in plugin_instance.actson['journals'].keys():
        if not self.journal_w.has_key(key):
          self.journal_w[key] = [(plugin_instance.name, plugin_instance.actson['journals'][key])]
        else:
          self.journal_w[key].append((plugin_instance.name, plugin_instance.actson['journals'][key]))
      self.status[plugin_instance.name] = True

  def handle(self, journal_name, path_to_nxml, components=['authors', 'citations', 'biblio', 'article_id'], force_plugin="", quiet=True):
    # TODO Handle + validate components before asking for it
    if force_plugin and force_plugin in self.plugins.keys():
      return self.plugins[force_plugin].gather_data(path_to_nxml, gather=components, quiet=quiet)
    
    if journal_name in self.journal_w.keys():
      sorted_plugins = sorted(self.journal_w[journal_name], key=itemgetter(1), reverse=True)
      # fallback parser = should always exist or this should really just crash out here
    else:
      sorted_plugins = []
    # Append glob plugins
    if self.journal_w.has_key("*"):
      sorted_plugins.extend(sorted(self.journal_w["*"], key=itemgetter(1), reverse=True))
    # Add the final fallback plugin
    fallback = self.journal_w["_fallback"][0]
    sorted_plugins.append(fallback)
    distribution = {}
    index = 0
    while(components and sorted_plugins):
      l_components = list(components)
      for x in l_components:
        if x in self.plugins[sorted_plugins[index][0]].provides.keys():
          if not distribution.has_key(sorted_plugins[index][0]):
            distribution[sorted_plugins[index][0]] = []
          distribution[sorted_plugins[index][0]].append(x)
          components.remove(x)
      index = index + 1
      if index == len(sorted_plugins):
        components = False
    data = {'_distribution':distribution, '_plugins':{}}
    for plugin, _ in sorted_plugins:
      if distribution.has_key(plugin):
        data['_plugins'][plugin] = {'name':self.plugins[plugin].name,
                        'repo':self.plugins[plugin].repo,
                        'version':self.plugins[plugin].version}
        resp = self.plugins[plugin].gather_data(path_to_nxml, 
                                              gather=distribution[plugin], 
                                              quiet=quiet)
        for x in distribution[plugin]:
          data[x] = resp[x]
    return data

