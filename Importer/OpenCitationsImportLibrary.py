#!/usr/bin/env python
# encoding: utf-8
"""
OpenCitationsImportLibrary.py

Created by Martyn Whitwell on 2013-02-08.
Based on arXiv MetaHarvester by Dr Heinrich Hartmann, related-work.net,  2012


"""

import sys, os, time
from datetime import date, datetime, timedelta
import dateutil.parser
from oaipmh.error import NoRecordsMatchError
from oaipmh.client import Client
from oaipmh.metadata import MetadataRegistry, oai_dc_reader
import MetadataReaders
import Batch
import Config
import hashlib, md5
import requests, json

class OAIImporter:

    METADATA_FORMAT_OAI_DC = {"prefix": 'oai_dc', "reader": oai_dc_reader}
    METADATA_FORMAT_PMC_FM = {"prefix": 'pmc_fm', "reader": MetadataReaders.MetadataReaderPMC()}
    METADATA_FORMAT_PMC = {"prefix": 'pmc', "reader": MetadataReaders.MetadataReaderPMC()}

    #default to OAI Dublin Core metadata format if note specified
    def __init__(self, uri, delta_days = 0, metadata = METADATA_FORMAT_OAI_DC):
        self.uri = uri
        self.delta_days = delta_days
        self.metadata = metadata
        self.es_synchroniser_config = Config.es_synchroniser_config_target + hashlib.md5(uri).hexdigest()

    def run(self):
        print "Importing from: %s" % self.uri

        registry = MetadataRegistry()
        registry.registerReader(self.metadata["prefix"], self.metadata["reader"])

        client = Client(self.uri, registry)
        identity = client.identify()

        print "Repository: %s" % identity.repositoryName()
        print "Metadata formats: %s" % client.listMetadataFormats()

        # got to update granularity or we barf with: 
        # oaipmh.error.BadArgumentError: Max granularity is YYYY-MM-DD:2003-04-10T00:00:00Z
        client.updateGranularity()

        #ElasticSearch batcher
        batcher = Batch.Batch()

        synchronisation_config = self.get_synchronisation_config()
        if False and synchronisation_config is not None and "to_date" in synchronisation_config:
            last_synchronised = dateutil.parser.parse(synchronisation_config["to_date"])
        else:
            last_synchronised = dateutil.parser.parse("2013-02-08")

        #total_records = 0

        #total_records += self.synchronise_record(client, batcher, "oai:arXiv.org:0804.2273")
        
        #return 1




        print "Last synchronised to: %s" % last_synchronised.date()
        if not (last_synchronised.date() < (date.today() - timedelta(days=1))):
            print "Nothing to synchronise today."
        
        start = time.time()
        while last_synchronised.date() < (date.today() - timedelta(days=1)):
            start_date = last_synchronised + timedelta(days=1)
            end_date = start_date + timedelta(days=self.delta_days)
            number_of_records = self.synchronise_by_block(client, batcher, start_date, end_date)
            self.put_synchronisation_config(start_date, end_date, number_of_records)
            last_synchronised = end_date
            total_records += number_of_records
        
        batcher.clear()
        time_spent = time.time() - start
        print 'Total time spent: %d seconds' % (time_spent)

        if time_spent > 0.001: # careful as its not an integer
            print 'Total records synchronised: %i records (%d records/second)' % (total_records, (total_records/time_spent))
        else:
            print 'Total records synchronised: %i records' % (total_records)
        return total_records
    



    def synchronise_by_block(self, client, batcher, start_date, end_date):
        print "Synchronising period: %s - %s" % (start_date, end_date)
        records = list(self.get_records(client, start_date, end_date))
        for record in records:
            batcher.add(self.bibify_record(record))
        return len(records)


    def synchronise_by_records(self, client, batcher, start_date, end_date):
        print "Synchronising records in period: %s - %s" % (start_date, end_date)
        identifiers = list(self.get_identifiers(client, start_date, end_date))
        counter = 0
        for identifier in identifiers:
            print "Synchronising %s - %s" % (identifier.identifier(), identifier.datestamp())
            record = self.get_record(client, identifier.identifier())
            batcher.add(self.bibify_record(record))
            counter += 1
        return counter


    def synchronise_record(self, client, batcher, oaipmh_identifier):
        print "Synchronising record: %s" % (oaipmh_identifier)
        record = self.get_record(client, oaipmh_identifier)
        batcher.add(self.bibify_record(record))
        return 1


    def get_synchronisation_config(self):
        print "Getting synchronisation_config for %s" % (self.uri)
        r = requests.get(self.es_synchroniser_config)
        if r.status_code == 404 or not r.json()["exists"]:
            print "No synchronisation_config found"
            return None
        else:
            return r.json()["_source"]


    def put_synchronisation_config(self, from_date, to_date, number_of_records):
        print "Putting synchronisation_config for %s to %s" % (self.uri, self.es_synchroniser_config)
        data = {'uri': self.uri, 'from_date': from_date.isoformat(), 'to_date': to_date.isoformat(), 'number_of_records': number_of_records}
        r = requests.put(self.es_synchroniser_config, data=json.dumps(data))




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

        print 'client.listIdentifiers(from_=',start_date,'until=',end_date,'metadataPrefix=',self.metadata["prefix"],'))'
        try:
            identifiers = list(client.listIdentifiers(
                from_          = start_date,  # yes, it is from_ not from
                until          = end_date,
                metadataPrefix = self.metadata["prefix"]
                ))
        except NoRecordsMatchError:
            identifiers = []

        d_time = time.time() - chunk_time
        print 'received %d identifiers in %d seconds' % (len(identifiers), d_time )
        chunk_time = time.time()

        return identifiers


    def get_records(self, client, start_date, end_date):
        print '****** Getting records ******'
        print 'from   : %s' % start_date.strftime('%Y-%m-%d')
        print 'until  : %s' % end_date.strftime('%Y-%m-%d')

        chunk_time = time.time()

        print 'client.listRecords(from_=',start_date,'until=',end_date,'metadataPrefix=',self.metadata["prefix"],'))'
        try:
            records = list(client.listRecords(
                from_          = start_date,  # yes, it is from_ not from
                until          = end_date,
                metadataPrefix = self.metadata["prefix"]
                ))
        except NoRecordsMatchError:
            records = []

        d_time = time.time() - chunk_time
        print 'received %d records in %d seconds' % (len(records), d_time )
        chunk_time = time.time()

        return records



    def get_record(self, client, oaipmh_identifier):
        return list(client.getRecord(
            identifier = oaipmh_identifier,
            metadataPrefix = self.metadata["prefix"]))


    def bibify_record(self, record):
        header, metadata, about = record
        bibjson = metadata.getMap()
        bibjson["oaipmh.identifier"] = header.identifier()
        bibjson["oaipmh.datestamp"] = header.datestamp().isoformat()
        bibjson["oaipmh.setSpec"] = header.setSpec()
        bibjson["oaipmh.isDeleted"] = header.isDeleted()

        bibjson['_id'] = hashlib.md5(header.identifier()).hexdigest() #Not sure about sense of MD5 hash
        bibjson["url"] = Config.bibjson_url + bibjson["_id"]
        bibjson['_collection'] = [Config.bibjson_creator + '_____' + Config.bibjson_collname]
        bibjson['_created'] = datetime.now().strftime("%Y-%m-%d %H%M"),
        bibjson['_created_by'] = Config.bibjson_creator
        if "identifier" not in bibjson:
            bibjson["identifier"] = []
        #bibjson["identifier"].append({"type":"bibsoup", "id":bibjson["_id"],"url":bibjson["url"]})

        return bibjson
        








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
            print 'Header identifier: %s - %s' % (header.identifier(), header.datestamp())
            #print 'Header datestamp: %s' % header.datestamp()
            #print 'Header setSpec: %s' % header.setSpec()
            #print 'Header isDeleted: %s' % header.isDeleted()




