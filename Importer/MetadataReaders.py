#!/usr/bin/env python
# encoding: utf-8
"""
MetadataReaders.py

Created by Martyn Whitwell on 2013-02-08.
Based on PubMedCentral Parser by Mark MacGillivray

Parses PubMed Central Front Matter (PMC-FM) and arXiv metadata

"""

from oaipmh import common
from lxml import etree

import logging
logger = logging.getLogger('importer')
hdlr = logging.FileHandler('importer.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr) 
logger.setLevel(logging.DEBUG)


class MetadataReaderAbstract(object):
    """Metadata reader abstract class containing methods for use in derived classes.
    """

    _namespaces={
        'oai': 'http://www.openarchives.org/OAI/2.0/',
        'nlmaa': 'http://dtd.nlm.nih.gov/2.0/xsd/archivearticle',
        'arXiv': 'http://arxiv.org/OAI/arXiv/',
        'xlink': 'http://www.w3.org/1999/xlink',
        'mml' : 'http://www.w3.org/1998/Math/MathML',
        'xsi': 'http://www.w3.org/2001/XMLSchema-instance'}

    def __init__(self):
        pass


    #Find methods ----------------
    def _find_element(self, current_element, xpath):
        if current_element is not None:
            return current_element.find(xpath, self._namespaces)
        else:
            return None

    def _find_element_xml(self, current_element, xpath):
        sought_element = self._find_element(current_element, xpath)
        if sought_element is not None:
            return etree.tostring(sought_element)
        else:
            return None


    #REPLACE WITH FINDTEXT()??
    def _find_element_text(self, current_element, xpath):
        sought_element = self._find_element(current_element, xpath)
        if sought_element is not None and hasattr(sought_element,'text') and sought_element.text is not None:
            return sought_element.text
        else:
            return None

    def _find_elements(self, current_element, xpath):
        if current_element is not None:
            return current_element.findall(xpath, self._namespaces)
        else:
            return [] #return empty list


    #Set methods ----------------
    def _set_map_with_element_text(self, map, key, current_element, xpath):
        value = self._find_element_text(current_element, xpath)
        if value is not None:
            map[key] = value
            return True
        else:
            return False

    def _set_map_with_element_xml(self, map, key, current_element, xpath):
        value = self._find_element_xml(current_element, xpath)
        if value is not None:
            map[key] = value
            return True
        else:
            return False





class MetadataReaderArXiv(MetadataReaderAbstract):
    """A metadata reader for arXiv.
    """

    def __call__(self, metadata_element):
        map = { 'identifier':[], 'journal':{}, 'author':[] }

        arXiv = self._find_element(metadata_element, "arXiv:arXiv")
        arXiv_id = self._find_element_text(arXiv, "arXiv:id")
        doi = self._find_element_text(arXiv, "arXiv:doi")
        
        if arXiv_id is not None:
            map["identifier"].append({'type':'arXiv', 'id':arXiv_id})
        if doi is not None:
            map["identifier"].append({'type':'doi', 'id':doi})

        #title
        self._set_map_with_element_text(map, "title", arXiv, "arXiv:title")

        #copyright ?
        #license
        self._set_map_with_element_text(map, "license", arXiv, "arXiv:license")
        
        #abstract
        self._set_map_with_element_text(map, "abstract", arXiv, "arXiv:abstract")

        #journal
        self._set_map_with_element_text(map['journal'], "reference", arXiv, "arXiv:journal-ref")
        self._set_map_with_element_text(map['journal'], "comments", arXiv, "arXiv:comments")
        self._set_map_with_element_text(map['journal'], "categories", arXiv, "arXiv:categories")


        #authors
        for author in self._find_elements(arXiv,"arXiv:authors/arXiv:author"):
            entity = {}
            self._set_map_with_element_text(entity, "lastname", author, "arXiv:keyname")
            self._set_map_with_element_text(entity, "forenames", author, "arXiv:forenames") #MW: Changed firstname to forenames. Discuss with Mark.
            self._set_map_with_element_text(entity, "suffix", author, "arXiv:suffix")
            if "lastname" in entity and entity["lastname"] is not None and "forenames" in entity and entity["forenames"] is not None:
                entity["name"] = entity["lastname"] + ", " + entity["forenames"]
            affiliations = self._find_elements(author,"arXiv:affiliation")
            if affiliations:
                entity["affiliation"] = []
                for affiliation in affiliations:
                    entity["affiliation"].append(affiliation.text)
            map["author"].append(entity)

        return common.Metadata(map)

    
    

class MetadataReaderPMC(MetadataReaderAbstract):
    """A metadata reader for PubMedCentral Front Matter data.
    """

    def __call__(self, metadata_element):
        map = {}

        # front
        front = self._find_element(metadata_element,"nlmaa:article/nlmaa:front")
        
        # back
        back = self._find_element(metadata_element,"nlmaa:article/nlmaa:back")

        # journal meta
        journal_meta = self._find_element(front,"nlmaa:journal-meta")
        
        # article metadata
        article_meta = self._find_element(front,"nlmaa:article-meta")
        
        if journal_meta is not None:
            try:
                map["journal"] = {}

                (self._set_map_with_element_text(map["journal"], "name", journal_meta, "nlmaa:journal-title-group/nlmaa:journal-title") or
                    self._set_map_with_element_text(map["journal"], "name", journal_meta, "nlmaa:journal-title"))
                
                issns = journal_meta.findall('nlmaa:issn', self._namespaces)
                if issns:
                    map["journal"]["identifier"] = []
                    for issn in issns:
                        map["journal"]["identifier"].append({"type": issn.get('pub-type'), "id": issn.text})
                
                self._set_map_with_element_text(map["journal"], "publisher", journal_meta, "nlmaa:publisher/nlmaa:publisher-name")
            except:
                logging.error("Could not extract journal metadata")
        else:
            logging.info("No journal metadata found for ")
        
        
        if article_meta is not None:
            try:
                #identifiers
                article_ids = article_meta.findall("nlmaa:article-id", self._namespaces)
                if article_ids:
                    map["identifier"] = []
                    for article_id in article_ids:
                        map["identifier"].append({"type": article_id.get('pub-id-type'), "id": article_id.text})
            except:
                logging.error("Could not extract identifiers from article metadata")
            
            try:
                #title
                self._set_map_with_element_text(map, "title", article_meta, "nlmaa:title-group/nlmaa:article-title")
            except:
                logging.error("Could not extract title from article metadata")
            
            try:
                #pagination
                self._set_map_with_element_text(map, "volume", article_meta, "nlmaa:volume")
                self._set_map_with_element_text(map, "issue", article_meta, "nlmaa:issue")
                self._set_map_with_element_text(map, "firstpage", article_meta, "nlmaa:fpage")
                self._set_map_with_element_text(map, "lastpage", article_meta, "nlmaa:lpage")
                if "firstpage" in map:
                    if "lastpage" in map and (map["firstpage"] != map["lastpage"]):
                        map["pages"] = map["firstpage"] + "-" + map["lastpage"]
                    else:
                        map["pages"] = map["firstpage"]
            except:
                logging.error("Could not extract pagination from article metadata")

            try:
                #publication date
                # why only use the pmc-release date? need to check with Mark
                pub_date = article_meta.find("nlmaa:pub-date[@pub-type='pmc-release']", self._namespaces)
                if pub_date is not None:
                    self._set_map_with_element_text(map, "year", pub_date, "nlmaa:year")
                    self._set_map_with_element_text(map, "month", pub_date, "nlmaa:month")
                    self._set_map_with_element_text(map, "day", pub_date, "nlmaa:day")
                else:
                    logging.info("No publication data for ")
            except:
                logging.error("Could not extract publication date from article metadata")
            
            try:
                #copyright
                self._set_map_with_element_text(map, "copyright", article_meta, "nlmaa:permissions/nlmaa:copyright-statement")
            except:
                logging.error("Could not extract copyright info from article metadata")
            
            try:
                #abstract
                self._set_map_with_element_xml(map, "abstract", article_meta, "nlmaa:abstract")
            except:
                logging.error("Could not extract abstract from article metadata")
            
            try:
                #keywords
                keywords = article_meta.findall("nlmaa:kwd_group/nlmaa:kwd", self._namespaces)
                if keywords:
                    map["keyword"] = []
                    for keyword in keywords:
                        map["keyword"].append(keyword.text)
                else:
                    logging.info("No keywords for ")
            except:
                logging.error("Could not extract keywords from article metadata")
            
            try:
                #contributors
                contribs = article_meta.findall("nlmaa:contrib-group/nlmaa:contrib", self._namespaces)
                if contribs:
                    map["author"] = []
                    map["editor"] = []
                    for contrib in contribs:
                        entity = {}
                        if contrib.get('corresp') == 'yes':
                            entity["corresponding"] = 'yes'
                        self._set_map_with_element_text(entity, "lastname", contrib, "nlmaa:name/nlmaa:surname")
                        self._set_map_with_element_text(entity, "forenames", contrib, "nlmaa:name/nlmaa:given-names") #MW: Changed firstname to forenames. Discuss with Mark.
                        if "lastname" in entity and entity["lastname"] is not None and "forenames" in entity and entity["forenames"] is not None:
                            entity["name"] = entity["lastname"] + ", " + entity["forenames"]
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
                else:
                    logging.info("No contributors found for ")
            except:
                logging.error("Could not extract contributors from article metadata")
        else:
            logging.info("No article metadata found for ")


        if back is not None:
            acknowledgements = back.findall("nlmaa:ack/nlmaa:sec/nlmaa:p", self._namespaces)
            if acknowledgements:
                map["acknowledgement"] = []
                for acknowledgement in acknowledgements:
                    map["acknowledgement"].append(acknowledgement.text)
            else:
                logging.info("No acknowledgements found for ")
            
            conflicts = back.findall("nlmaa:fn-group/nlmaa:fn/nlmaa:p", self._namespaces)
            if conflicts:
                map["conflict"] = []
                for conflict in conflicts:
                    map["conflict"].append(conflict.text)
            else:
                logging.info("No conflicts found for ")
                    
            refs = back.findall("nlmaa:ref-list/nlmaa:ref", self._namespaces)
            if refs:
                map["citation"] = []
                for ref in refs:
                    entity = {}
                    self._set_map_with_element_text(entity, "label", ref, "nlmaa:label")
                    
                    #Three different ways to cite articles. Check with Mark.
                    citation = ref.find("nlmaa:mixed-citation", self._namespaces)
                    if citation is None:
                        citation = ref.find("nlmaa:element-citation", self._namespaces)
                    if citation is None:
                        citation = ref.find("nlmaa:citation", self._namespaces)
                    
                    if citation is not None:
                        self._set_map_with_element_text(entity, "title", citation, "nlmaa:article-title")
                        pub_ids = citation.findall("nlmaa:pub-id", self._namespaces)
                        if pub_ids:
                            entity["identifier"] = []
                            for pub_id in pub_ids:
                                entity["identifier"].append({"type": pub_id.get('pub-id-type'), "id": pub_id.text})
                    # TODO: should this append happen even if the entity is empty? or bring into the above IF
                    map["citation"].append(entity)
                    # add code here to create a record for this citation if it does not already exist
            else:
                logging.info("No refs found for ")
        else:
            logging.info("No back metadata for ")


        return common.Metadata(map)

