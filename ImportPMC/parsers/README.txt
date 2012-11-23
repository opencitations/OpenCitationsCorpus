PubMed plugin system:
---------------------

The base.py class implements the main plugin system from which all of the parsers subclass.

The model is that each parser provides a list of Journals which they can handle and the ‘confidence’ or weight that they can parse said Journal nxml (set up in __init__ within ‘self.actson’. 

They also provide a list of components that can be retrieved, with a comment that describes roughly the data that component extracts. (within ‘self.provides’)

For example: (formatted for readability)

class Fallback(PubMedParser):
  def __init__(self):
    self.name = "Fallback"
    self.actson = {'journals':{'*':100}} # acts on * with weight 100
    self.provides = {'authors':'A list of authors in order, if one exists',
                     'citations':’List of citation information in the order\ 
                                  it occurs. Returns source, title, author\
                                  list, date if found',
                     'full_biblio':'full bibliographic data, as far as that      
                                    is possible for the article itself'}


The weighting is used by the plugin manager, which aims to select the highest weighted plugin to get the component desired from the given journal article. For example:

Plugin 1: Journal A at confidence:100 - provides id, biblio, and citations
Plugin 2: Journal A, 250 - provides citations

>>> plugin_manager.handle(”JournalA”, “....nxml”, [’biblio’, ‘citations’])

this should reply:

{’biblio’:{’parser’:’Plugin 1’ ...data..}, 
 ‘citations’:{’parser’:’Plugin 2’..data..},}

(NB currently, the plugin manager just picks the highest ranked plugin for all components - this is being changed right now!)

Writing your own plugin:
------------------------

Basic Skeleton:

----->

from base import PubmedParser

...

class MyPlugin(PubmedParser):
  def plugin_warmup(self):
    """ Do two things here: 1) set some properties to describe the plugin and
    2) warm up or connection to any caches, indexes or lookup tables that this
    instance will need.
 
    If anything goes wrong, or a vital client cannot be configured, throw an Exception.

    for 1) set the following:"""

    name = "PluginName” # make this unique to your plugin
    actson = {'journals':{'Journal Short Name':100}}

    #     (eg ‘PLoS_Med’:100, ‘BMC_Bioinformatics’: 50, ..)
    #     'journals' dict key = Name of journal directory, value = confidence/preference (higher = better)

    version = Version number of code - can be hg/git HEAD id

    repo = URL to code repository

    """ 2) - do things to set up the plugin - perform all the mysql or sparql connection inits, name resolution logins, etc here. Raising an exception here will cause the plugin manager to mark the plugin as ‘failed’ and will remove it from selection.
    """
    pass

  # write the components you want this parser to provide, like a set of citation authors, 'cited by' lookups for all the citations in the paper, and so on

  # Preface a component method with '_comp_' and give it an inline comment. It will automatically be picked up and made available
  # eg 
  
  def _comp_get_emails(self, d, quiet=True):
    """This string will be inspected and put into the main description for this component"""
    # d - lxml etree object for the given NLM xml file
    ...
    return some_data_object
    
  # in self.provides dict there will be a key of 'get_emails' with value 'This string... nent', amongst any other components this plugin provides.

<----


