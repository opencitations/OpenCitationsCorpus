#!/usr/bin/env python
# encoding: utf-8
"""
OpenCitationsImportLibrary.py

Created by Martyn Whitwell on 2013-02-08.
Based on arXiv MetaHarvester by Dr Heinrich Hartmann, related-work.net,  2012

"""

import sys
import os
import time
from datetime import date, datetime, timedelta
from oaipmh.client import Client
from oaipmh.metadata import MetadataRegistry, MetadataReader#, oai_dc_reader
from lxml import etree
from lxml.etree import SubElement
from oaipmh import common
import Parse


class MetadataReaderPMCFM(object):

    _namespaces={
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

        print "XML ELEMENT---------"
        print(etree.tostring(metadata_element, pretty_print=True))

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
                    if "lastname" in entity and "firstname" in entity:
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





class OAIImporter:

    METADATA_PREFIX_OAI_DC = 'oai_dc'
    METADATA_PREFIX_PMC_FM = 'pmc_fm'
    METADATA_PREFIX_PMC = 'pmc'

    METADATA_READER_OAI_DC = MetadataReader(
        fields={
        'title':       ('textList', 'oai_dc:dc/dc:title/text()'),
        'creator':     ('textList', 'oai_dc:dc/dc:creator/text()'),
        'subject':     ('textList', 'oai_dc:dc/dc:subject/text()'),
        'description': ('textList', 'oai_dc:dc/dc:description/text()'),
        'publisher':   ('textList', 'oai_dc:dc/dc:publisher/text()'),
        'contributor': ('textList', 'oai_dc:dc/dc:contributor/text()'),
        'date':        ('textList', 'oai_dc:dc/dc:date/text()'),
        'type':        ('textList', 'oai_dc:dc/dc:type/text()'),
        'format':      ('textList', 'oai_dc:dc/dc:format/text()'),
        'identifier':  ('textList', 'oai_dc:dc/dc:identifier/text()'),
        'source':      ('textList', 'oai_dc:dc/dc:source/text()'),
        'language':    ('textList', 'oai_dc:dc/dc:language/text()'),
        'relation':    ('textList', 'oai_dc:dc/dc:relation/text()'),
        'coverage':    ('textList', 'oai_dc:dc/dc:coverage/text()'),
        'rights':      ('textList', 'oai_dc:dc/dc:rights/text()')
        },
        namespaces={
        'oai_dc': 'http://www.openarchives.org/OAI/2.0/oai_dc/',
        'dc' : 'http://purl.org/dc/elements/1.1/'}
        )

    METADATA_READER_PMC_FM = MetadataReaderPMCFM()


    def run(self):
        print "Importing from: %s" % self.uri
        print "From date: %s" % self.from_date
        print "Until date: %s" % self.until_date
        print "Delta months: %s" % self.delta_months

        registry = MetadataRegistry()
        registry.registerReader(self.metadata_prefix, self.metadata_reader)

        client = Client(self.uri, registry)
        identity = client.identify()

        print "Repository: %s" % identity.repositoryName()
        print "Metadata formats: %s" % client.listMetadataFormats()

        # got to update granularity or we barf with: 
        # oaipmh.error.BadArgumentError: Max granularity is YYYY-MM-DD:2003-04-10T00:00:00Z
        client.updateGranularity()
    
        # register a reader on our client to handle oai_dc metadata
        # if we do not attempt to read records will fail with:
        #   .../oaipmh/metadata.py", line 37, in readMetadata
        #   KeyError: 'oai_dc'
        #client.getMetadataRegistry().registerReader('oai_dc', oai_dc_reader)

        start = time.time()
        #for (current_date, next_date) in self.loop_months():
            #print "current_date: %s, next_date: %s" % (current_date, next_date)

            # get identifiers
            #identifiers = list(self.get_identifiers(client, current_date, next_date))
            #self.print_identifiers(identifiers)
            
            # get records
            #try:
            #    records = list(self.get_records(client, current_date, next_date))
            #except:
            #    print "failed receiving records!"
            #    continue
            #self.print_records(records, max_recs = 2)

        record = self.get_record(client)
        self.print_record(record)

        print 'Total Time spent: %d seconds' % (time.time() - start)



    def loop_months(self):
        if self.delta_months == 0: return

        current_date = self.from_date
        while True:
            if self.delta_months > 0 and current_date >= self.until_date: break
            if self.delta_months < 0 and current_date <= self.until_date: break
    
            carry, new_month = divmod(current_date.month - 1 + self.delta_months, 12)
            new_month += 1
            next_date = current_date.replace(year=current_date.year + carry, month=new_month)
        
            if self.delta_months > 0 and next_date > self.until_date: next_date = self.until_date
            if self.delta_months < 0 and next_date < self.until_date: next_date = self.until_date

            if self.delta_months > 0: 
                yield current_date, next_date
            if self.delta_months < 0: 
                yield next_date, current_date

            current_date = next_date

    def get_identifiers(self, client, start_date, end_date):
        print '****** Getting identifiers ******'
        print 'from   : %s' % start_date.strftime('%Y-%m-%d')
        print 'until  : %s' % end_date.strftime('%Y-%m-%d')

        chunk_time = time.time()

        print 'client.listIdentifiers(from_=',start_date,'until=',end_date,'metadataPrefix=',self.metadata_prefix,'))'
        identifiers = list(client.listIdentifiers(
                from_          = start_date,  # yes, it is from_ not from
                until          = end_date,
                metadataPrefix = self.metadata_prefix
                ))

        d_time = time.time() - chunk_time
        print 'received %d identifiers in %d seconds' % (len(identifiers), d_time )
        chunk_time = time.time()

        return identifiers


    def get_records(self, client, start_date, end_date):
        print '****** Getting records ******'
        print 'from   : %s' % start_date.strftime('%Y-%m-%d')
        print 'until  : %s' % end_date.strftime('%Y-%m-%d')

        chunk_time = time.time()

        print 'client.listRecords(from_=',start_date,'until=',end_date,'metadataPrefix=',self.metadata_prefix,'))'
        records = list(client.listRecords(
                from_          = start_date,  # yes, it is from_ not from
                until          = end_date,
                metadataPrefix = self.metadata_prefix
                ))

        d_time = time.time() - chunk_time
        print 'recieved %d records in %d seconds' % (len(records), d_time )
        chunk_time = time.time()

        return records



    def get_record(self, client):
        print '****** Getting 1 record ******'

        chunk_time = time.time()
        record = list(client.getRecord(
                identifier = 'oai:pubmedcentral.nih.gov:3081214',
                metadataPrefix = self.metadata_prefix
                ))

        d_time = time.time() - chunk_time
        print 'recieved in %d seconds' % (d_time )
        chunk_time = time.time()

        return record


    def print_records(self, records, max_recs = 2):
        print '****** Printing data ******'
        # for large collections this breaks
        count = 1

        for record in records:
            header, metadata, about = record
            map = metadata.getMap()
            print '****** Current record count: %i' % count
            print 'Header identifier: %s' % header.identifier()
            print 'Header datestamp: %s' % header.datestamp()
            print 'Header setSpec: %s' % header.setSpec()
            print 'Header isDeleted: %s' % header.isDeleted()
            print "KEYS+VALUES"
            for key, value in map.items():
                print '  ', key, ':', value
            print ""
            if count > max_recs: break
            count += 1


    def print_record(self, record):
        header, metadata, about = record
        map = metadata.getMap()
        print 'Header identifier: %s' % header.identifier()
        print 'Header datestamp: %s' % header.datestamp()
        print 'Header setSpec: %s' % header.setSpec()
        print 'Header isDeleted: %s' % header.isDeleted()
        print "KEYS+VALUES"
        for key, value in map.items():
            print '  ', key, ':', value
        print ""


    def print_identifiers(self, identifiers, max_recs = 20):
        print '****** Printing identifiers ******'
        # for large collections this breaks
        count = 1

        for header in identifiers:
            print 'Header identifier: %s' % header.identifier()
            print 'Header datestamp: %s' % header.datestamp()
            print 'Header setSpec: %s' % header.setSpec()
            print 'Header isDeleted: %s' % header.isDeleted()


    def __init__(self, uri, from_date, until_date, delta_months = 1, metadata_prefix = METADATA_PREFIX_OAI_DC):
        self.uri = uri
        self.from_date = datetime.strptime(from_date,"%Y-%m-%d")
        self.until_date = datetime.strptime(until_date,"%Y-%m-%d")
        self.delta_months = delta_months
        self.metadata_prefix = metadata_prefix
        self.metadata_reader = self.METADATA_READER_PMC_FM

