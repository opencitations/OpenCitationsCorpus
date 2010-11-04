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

- Subclass from base.PubMedParser
- Main methods: plugin_warmup and methods beginning with '_comp_'
- In plugin_warmup, set the following attributes:
   name = "PluginName” # make this unique
   actson = {'journals':{'Journal Short Name':100 # confidence, etc}}
       (eg ‘PLoS_Med’:100, ‘BMC_Bioinformatics’: 50, ..)
   version = Version number of code - can be hg/git HEAD id
   repo = URL to code repository
   - perform all the mysql or sparql connection inits, name resolution logins, etc here. Raising an exception here will cause the plugin manager to mark the plugin as ‘failed’ and will remove it from selection.

Expected reply is a dict of values that must contain the following:

   {’parser’:’Parser name’, ‘component1’:{ data },
                            ‘component2’:{ data },
                            etc }
         Where ‘component1’ is the name of the requested component.

-- Providing components in your plugin --

Simply add a method beginning with '_comp_' and it will automatically show up as a 
provided plugin method.

The plugin manager will also retrieve the method description for display through the plugin
or the plugin manager.

eg:

  def _comp_get_emails(self, d, quiet=True):
    """This string will be inspected and put into the main description for this component"""
    # d - lxml etree object for the given NLM xml file
    ...
    return some_data_object
    
in self.provides will contain 'get_emails':'This string... nent', amongst any other
components this plugin provides.
