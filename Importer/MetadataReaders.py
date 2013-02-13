#!/usr/bin/env python
# encoding: utf-8
"""
OpenCitationsImportLibrary.py

Created by Martyn Whitwell on 2013-02-08.
Based on PubMedCentral Parser by Mark MacGillivray

"""

from oaipmh import common
from lxml import etree


class MetadataReaderPMC(object):

    _namespaces={
        'oai': 'http://www.openarchives.org/OAI/2.0/',
        'nlmaa': 'http://dtd.nlm.nih.gov/2.0/xsd/archivearticle',
        'xlink': 'http://www.w3.org/1999/xlink',
        'mml' : 'http://www.w3.org/1998/Math/MathML',
        'xsi': 'http://www.w3.org/2001/XMLSchema-instance'}

    """A metadata reader for PubMedCentral Front Matter data.
    """
    def __init__(self):
        pass

    def set_map_with_element_text(self, map, key, element, xpath):
        if element is not None:
            sought_element = element.find(xpath, self._namespaces)
            if sought_element is not None and hasattr(sought_element,'text'):
                map[key] = sought_element.text
                return True
        return False

    def set_map_with_element_xml(self, map, key, element, xpath):
        if element is not None:
            sought_element = element.find(xpath, self._namespaces)
            if sought_element is not None:
                map[key] = etree.tostring(sought_element)
                return True
        return False
        
        

    def __call__(self, metadata_element):
        map = {}
        #map = self._prepdoc()

        # front
        front = metadata_element.find("nlmaa:article/nlmaa:front", self._namespaces)

        # back
        back = metadata_element.find("nlmaa:article/nlmaa:back", self._namespaces)

        # journal meta
        journal_meta = front.find("nlmaa:journal-meta", self._namespaces)
        
        # article metadata
        article_meta = front.find("nlmaa:article-meta", self._namespaces)
        
        if journal_meta is not None:
            
            map["journal"] = {}

            (self.set_map_with_element_text(map["journal"], "name", journal_meta, "nlmaa:journal-title-group/nlmaa:journal-title") or
                self.set_map_with_element_text(map["journal"], "name", journal_meta, "nlmaa:journal-title"))
            
            issns = journal_meta.findall('nlmaa:issn', self._namespaces)
            if issns:
                map["journal"]["identifier"] = []
                for issn in issns:
                    map["journal"]["identifier"].append({"type": issn.get('pub-type'), "id": issn.text})
            
            self.set_map_with_element_text(map["journal"], "publisher", journal_meta, "nlmaa:publisher/nlmaa:publisher-name")
        
        if article_meta is not None:
    
            #identifiers
            article_ids = article_meta.findall("nlmaa:article-id", self._namespaces)
            if article_ids:
                map["identifier"] = []
                for article_id in article_ids:
                    map["identifier"].append({"type": article_id.get('pub-id-type'), "id": article_id.text})
            
            #title
            self.set_map_with_element_text(map, "title", article_meta, "nlmaa:title-group/nlmaa:article-title")
            
            #pagination
            self.set_map_with_element_text(map, "volume", article_meta, "nlmaa:volume")
            self.set_map_with_element_text(map, "issue", article_meta, "nlmaa:issue")
            self.set_map_with_element_text(map, "firstpage", article_meta, "nlmaa:fpage")
            self.set_map_with_element_text(map, "lastpage", article_meta, "nlmaa:lpage")
            if "firstpage" in map:
                if "lastpage" in map and (map["firstpage"] != map["lastpage"]):
                    map["pages"] = map["firstpage"] + "-" + map["lastpage"]
                else:
                    map["pages"] = map["firstpage"]

            #publication date
            # why only use the pmc-release date? need to check with Mark
            pub_date = article_meta.find("nlmaa:pub-date[@pub-type='pmc-release']", self._namespaces)
            if pub_date is not None:
                self.set_map_with_element_text(map, "year", pub_date, "nlmaa:year")
                self.set_map_with_element_text(map, "month", pub_date, "nlmaa:month")
                self.set_map_with_element_text(map, "day", pub_date, "nlmaa:day")
            
            #copyright
            self.set_map_with_element_text(map, "copyright", article_meta, "nlmaa:permissions/nlmaa:copyright-statement")
            
            #abstract
            self.set_map_with_element_xml(map, "abstract", article_meta, "nlmaa:abstract")
            
            #keywords
            keywords = article_meta.findall("nlmaa:kwd_group/nlmaa:kwd", self._namespaces)
            if keywords:
                map["keyword"] = []
                for keyword in keywords:
                    map["keyword"].append(keyword.text)
            
            #contributors
            contribs = article_meta.findall("nlmaa:contrib-group/nlmaa:contrib", self._namespaces)
            
            if contribs:
                map["author"] = []
                map["editor"] = []
                for contrib in contribs:
                    entity = {}
                    if contrib.get('corresp') == 'yes':
                        entity["corresponding"] = 'yes'
                    self.set_map_with_element_text(entity, "lastname", contrib, "nlmaa:name/nlmaa:surname")
                    self.set_map_with_element_text(entity, "firstname", contrib, "nlmaa:name/nlmaa:given-names")
                    if "lastname" in entity and entity["lastname"] is not None and "firstname" in entity and entity["firstname"] is not None:
                        entity["name"] = entity["lastname"] + " " + entity["firstname"]
                    email = contrib.find("nlmaa:address/nlmaa:email", self._namespaces)
                    if email is None:
                        email = contrib.find("nlmaa:email", self._namespaces)
                    if email is not None:
                        entity["identifier"] = {"type": "email", "id": email.text}
                    
                    xrefs = contrib.findall("nlmaa:xref", self._namespaces)
                    affs = article_meta.findall("nlmaa:aff", self._namespaces) #NOT ContribGroup - check with Mark
                    for xref in xrefs:
                        if xref.get('ref-type') == "aff":
                            rid = xref.get("rid")
                            for aff in affs:
                                if aff.get("id") == rid:
                                    if "affiliation" not in entity:
                                        entity["affiliation"] = []
                                    for text in aff.itertext():
                                        entity["affiliation"].append(text)
                                    
                    if contrib.get("contrib-type") == "author":
                        map["author"].append(entity)
                    if contrib.get("contrib-type") == "editor":
                        map["editor"].append(entity)

        if back is not None:
            acknowledgements = back.findall("nlmaa:ack/nlmaa:sec/nlmaa:p", self._namespaces)
            if acknowledgements:
                map["acknowledgement"] = []
                for acknowledgement in acknowledgements:
                    map["acknowledgement"].append(acknowledgement.text)
            
            conflicts = back.findall("nlmaa:fn-group/nlmaa:fn/nlmaa:p", self._namespaces)
            if conflicts:
                map["conflict"] = []
                for conflict in conflicts:
                    map["conflict"].append(conflict.text)
                    
            refs = back.findall("nlmaa:ref-list/nlmaa:ref", self._namespaces)
            if refs:
                map["citation"] = []
                for ref in refs:
                    entity = {}
                    self.set_map_with_element_text(entity, "label", ref, "nlmaa:label")
                    
                    #Three different ways to cite articles. Check with Mark.
                    citation = ref.find("nlmaa:mixed-citation", self._namespaces)
                    if citation is None:
                        citation = ref.find("nlmaa:element-citation", self._namespaces)
                    if citation is None:
                        citation = ref.find("nlmaa:citation", self._namespaces)
                    
                    if citation is not None:
                        self.set_map_with_element_text(entity, "title", citation, "nlmaa:article-title")
                        pub_ids = citation.findall("nlmaa:pub-id", self._namespaces)
                        if pub_ids:
                            entity["identifier"] = []
                            for pub_id in pub_ids:
                                entity["identifier"].append({"type": pub_id.get('pub-id-type'), "id": pub_id.text})
                    map["citation"].append(entity)



        return common.Metadata(map)

