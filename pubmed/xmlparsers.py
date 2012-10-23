#
# Module for handling Paper-metadata and References from PubMed central
#
# by Heinrich Hartmann, 2012
#
# License: CC-SA
#
# This work is part of related-work.net
#
"""
This module provides classes (Paper and Reference) to handle 
xml-metadata procided by pubmed central
"""

from lxml import etree

class Paper(object):
    """
    Handles paper records constructed from nxml files.

    Attributes:
    * meta -- meta data following bibjson format (http://www.bibjson.org/)
    * ids  -- dictionary containing all ids provided by the paper
    """

    def __init__(self, fh):
        try:
            self.xml = etree.parse(fh)
            fh.close()
        except etree.XMLSyntaxError:
            raise SyntaxError('Error parsing xml file.')

        try:
            self.meta     = self._get_meta_dict(self.xml)
            self.abstract = self._get_abstract(self.xml)
        except KeyError:
            raise SyntaxError('Malformatted xml file. Cannot extract metadata.')
        
        # convenience attributes
        self.ids     = dict( (ID['type'], ID['id']) for ID in self.meta['identifier'] )
        self.title   = self.meta['title']
        self.author  = self.meta['author']
        self.year    = self.meta['year']
        self.journal = self.meta['journal']['shortcode']


    def get_references(self):
        for cite_elt in self.xml.findall('/back/ref-list/ref/mixed-citation'):
            try:
                ref = Reference(cite_elt)
            except SyntaxError:
                continue

            yield ref


    def _get_meta_dict(self, xml):
        meta_elt = xml.find('/front/article-meta')
        meta = {
            'title'      : meta_elt.findtext('./title-group/article-title'),
            'author'     : [ u"{0}, {1}".format(name.findtext('surname'),
                                                name.findtext('given-names')).strip()
                             for name in meta_elt.findall('./contrib-group/contrib[@contrib-type="author"]/name')],
            'type'       : "article",
            # Remark: records contain several different publication dates. 
            # We choose the first one in order of the file
            'year'       : meta_elt.findtext('./pub-date/year'),
            'identifier' : [ { 'type': elt.attrib['pub-id-type'], 'id': elt.text }
                             for elt in meta_elt.findall('./article-id') ],
            'journal'    : {},
            }

        try:
            meta['journal'] = {
                'name'      : xml.findtext('/front/journal-meta/journal-title-group/journal-title'),
                'shortcode' : xml.findtext('/front/journal-meta/journal-id')
                }
        except AttributeError:
            self.journal = {}

        return meta


    def _get_abstract(self, xml):
        abstract = ''
        try:
            abstract = " ".join( 
                (x.text if x.text else "") + (x.tail if x.tail else "") 
                for x in  xml.find('/front/article-meta/abstract').iter()
                ).strip()
        except AttributeError:
            # no abstract element: abstract = ''
            pass

        return abstract

class Reference(object):
    """
    Container object for references found in nxml files.

    Input: 
    mixed-citation-xml as etree object

    Attributes:
    * meta       -- available metadata in bibjson format
    * string     -- as found in the reference list
    * ids        -- available ids as dictionary
    """

    def __init__(self,xml):
        # store values
        self.xml = xml

        # Find type of publication: journal-article / book / other
        try:
            self.type = xml.attrib['publication-type']
        except KeyError:
            raise SyntaxError('Publication-type not defined.')

        # Fill in meta-dict in bibjson standard
        self.meta   = self._get_meta_dict(xml)
        self.string = self._get_ref_string(self.meta)

        # Abbreviations
        self.ids     = dict( (ID['type'], ID['id']) for ID in self.meta['identifier'] )
        self.title   = self.meta['title']
        self.author  = self.meta['author']
        self.year    = self.meta['year']
        
    def __str__(self):
        # give back reference string, if object is called as string
        return self.string

    def _get_meta_dict(self,cite_xml):
        # Common meta attributes
        meta = {
            'title'      : '', # filled below
            'author'     : [ u"{0}, {1}".format(name.findtext('surname'),
                                                name.findtext('given-names')).strip()
                             for name in cite_xml.findall('./person-group[@person-group-type="author"]/name')],
            'type'       : self.type,
            'year'       : cite_xml.findtext('./year'),
            'identifier' : [ { 'type': pub_id.attrib['pub-id-type'], 'id': pub_id.text.strip() } 
                             for pub_id in cite_xml.findall('./pub-id') ],
            }

        # Type specific meta entries
        if self.type == 'journal':
            meta['title']     = cite_xml.findtext('./article-title')
            meta['journal']   = cite_xml.findtext('./source')
        elif self.type == 'book':
            meta['title']     = cite_xml.findtext('./source')
            meta['publisher'] = \
            ( cite_xml.findtext('./publisher-name') if cite_xml.findtext('./publisher-name') else "" ) + \
            ( " - " + cite_xml.findtext('./publisher-loc') if cite_xml.findtext('./publisher-loc') else "" )

        # Repair empty entries
        if meta['author'] == []:
            meta['author'] = [ u"%s, %s" % (name.findtext('surname'), 
                                            name.findtext('given-names'))
                               for name in cite_xml.findall('.//name') ]
        if meta['title']  in ("", None):
            meta['title'] = cite_xml.findtext('.//article-title')

        return meta


    def _get_ref_string(self, meta):
        if meta['type'] == "journal":
            ref_string = u"{author}, {title}, {journal} ({year})".format(
                author  = ' and '.join(meta['author']),
                title   = meta['title'],
                journal = meta['journal'],
                year    = meta['year'],
                )

        elif self.type == "book":
            ref_string = u"{author}, {title}, {publisher} ({year})".format(
                author    = ' and '.join(meta['author']),
                title     = meta['title'],
                publisher = meta['publisher'],
                year      = meta['year']
                )

        else: 
            # concatenate all entries in xml-file
            ref_string = u" ".join((
                    # xml.text
                    (self.xml.text if self.xml.text else u''),
                    # text of all childs
                    u" ".join(
                        (x.text.strip().replace('\n',' ') if x.text else '')
                        for x in self.xml.findall('.//*')
                        )
                    ))

        return ref_string.encode('UTF-8')


#
# BACKUP: nxml file format description
#
#
# Structure
# * front
#   * journal-meta
#     * journal-id
#  * article-meta
#    * article-id
#    * title-group
#      * article-title
#    * contrib-group
#      * contrib
#        * name
#          * surname
#          * given-names
#     * pub-date
# * body
#   (here comes the whole article)
# * back
#   * reflist
#     * mixed-citation
#       * person-name-group
#         * name
#           * surname
#           * given-names
#     * article-title
#     * source
#     * year
#     * pub-id
