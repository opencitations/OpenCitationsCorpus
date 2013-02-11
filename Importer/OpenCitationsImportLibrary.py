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

class MetadataReaderPMCFM(object):
    """A metadata reader for PubMedCentral Front Matter data.
    """
    def __init__(self, fields, namespaces=None):
        self._fields = fields
        self._namespaces = namespaces or {}

    def __call__(self, element):
        map = {}

        # create XPathEvaluator for this element
        xpath_evaluator = etree.XPathEvaluator(element, 
                                               namespaces=self._namespaces)
        
        e = xpath_evaluator.evaluate
        # now extra field info according to xpath expr
        for field_name, (field_type, expr) in self._fields.items():
            if field_type == 'bytes':
                value = str(e(expr))
            elif field_type == 'bytesList':
                value = [str(item) for item in e(expr)]
            elif field_type == 'text':
                # make sure we get back unicode strings instead
                # of lxml.etree._ElementUnicodeResult objects.
                value = unicode(e(expr))
            elif field_type == 'textList':
                # make sure we get back unicode strings instead
                # of lxml.etree._ElementUnicodeResult objects.
                value = [unicode(v) for v in e(expr)]
            else:
                raise Error, "Unknown field type: %s" % field_type
            map[field_name] = value
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

    METADATA_READER_PMC_FM = MetadataReaderPMCFM(
        fields={
        'title':       ('text', 'pmc:article/pmc:front/pmc:article-meta/pmc:title-group/pmc:article-title/text()'),
        'contrib' :    ('textList', 'pmc:article/pmc:front/pmc:article-meta/pmc:contrib-group/pmc:contrib/pmc:name/pmc:surname/text()'),

        'doi':       ('text', 'pmc:article/pmc:front/pmc:article-meta/pmc:article-id[@pub-id-type="doi"]/text()')
        },
        namespaces={
        'pmc': 'http://dtd.nlm.nih.gov/2.0/xsd/archivearticle',
        'xlink': 'http://www.w3.org/1999/xlink',
        'mml' : 'http://www.w3.org/1998/Math/MathML',
        'xsi': 'http://www.w3.org/2001/XMLSchema-instance'}
        )

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
                identifier = 'oai:pubmedcentral.nih.gov:29057',
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

