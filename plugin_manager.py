#!/usr/bin/env python
# -*- coding=utf-8 -*-

from parsers import *

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
    print "Registering %s" % plugin_instance
    try:
      plugin_instance.plugin_warmup()
      assert plugin_instance.name != None
      assert isinstance(plugin_instance.actson, dict)
      assert isinstance(plugin_instance.provides, dict)
      assert plugin_instance.version != None
      assert plugin_instance.repo != None
      assert plugin_instance.actson.has_key('journals')
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
          self.journal_w[key] = {plugin_instance.name:plugin_instance.actson['journals'][key]}
        else:
          self.journal_w[key][plugin_instance.name] = plugin_instance.actson['journals'][key]
      self.status[plugin_instance.name] = True

  def handle(self, journal_name, path_to_nxml, components=['authors', 'citations', 'biblio', 'article_id'], force_plugin="", quiet=True):
    # TODO Handle + validate components before asking for it
    if force_plugin and force_plugin in self.plugins.keys():
      return self.plugins[force_plugin].gather_data(path_to_nxml, gather=components, quiet=quiet)
    if journal_name in self.journal_w.keys():
      valid_plugins = self.journal_w[journal_name]
      maxweight = 0
      plugin_name = ""
      for v_plugin, weight in valid_plugins:
        if weight >= maxweight and self.status[plugin_name] == True:
          plugin_name = v_plugin
          maxweight = weight
      if plugin_name:
        return self.plugins[plugin_name].gather_data(path_to_nxml, gather=components, quiet=quiet)
      else:
        raise NoValidPlugin
    else:
      # fallback parser = should always exist or this should really just crash out here
      fallback = self.journal_w["*"].keys()[0]
      return self.plugins[fallback].gather_data(path_to_nxml, gather=components, quiet=quiet)

