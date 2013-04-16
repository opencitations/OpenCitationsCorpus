#!/usr/bin/env python
# encoding: utf-8
"""
OpenCitationsImportLibrary.py

Created by Martyn Whitwell on 2013-02-08.
Based on arXiv MetaHarvester by Dr Heinrich Hartmann, related-work.net,  2012

PMCBulkImporter and supporting classes added by Mark MacGillivray, 2013-03-06.

to run, you will need the following Python libraries
pip install python-dateutil
pip install pyoai
pip install lxml (and probably libxslt2-dev and libxml on your machine)
pip install -U requests #Upgrades to the latest version of requests

"""

import sys, os, time, requests, json, tarfile, shutil
from datetime import date, datetime, time as _time, timedelta
import dateutil.parser
from oaipmh.error import NoRecordsMatchError, IdDoesNotExistError
from oaipmh.client import Client
from oaipmh.metadata import MetadataRegistry, oai_dc_reader
import MetadataReaders
import Batch
import Config
import hashlib, md5
import requests, json
import uuid
from string import lstrip
sys.path.append('../ImportArxiv/tools')  #TODO: Tidy this up
import file_queue as fq
from nb_input import nbRawInput
from subprocess import call
import threading, Queue
from lxml import etree as ET


filejobs = Queue.Queue()


class ImporterAbstract(object): 
    # Generic methods used by OAI-feed Importer and PMCBulkImporter

    def check_index(self):
        # check that ElasticSearch is awake
        try:
            r = requests.get(Config.elasticsearch['uri_base'])
            if r.status_code != 200:
                print "The elasticsearch index %s responded with an unexpected status %s. Aborting." % (Config.elasticsearch['uri_base'], r.status_code)
                sys.exit(1)
        except:
            print "There is no elasticsearch index available at %s. Aborting." % Config.elasticsearch['uri_base']
            sys.exit(1)


    def rebuild_index(self):
        # check that ElasticSearch is awake
        self.check_index()

        print "Deleting type: %s" % (Config.elasticsearch['type_record'])
        r = requests.delete(Config.elasticsearch['uri_records'])
        print "...response from: %s (%s)" % (r.url, r.status_code)

        print "Deleting type: %s" % (Config.elasticsearch['type_config'])
        r = requests.delete(Config.elasticsearch['uri_configs'])
        print "...response from: %s (%s)" % (r.url, r.status_code)

        # check to see if index exists - in which case it will have a mapping even if it is empty, create if not
        if requests.get(Config.elasticsearch['uri_index'] + '/_mapping').status_code == 404:
            print "Creating index: %s" % (Config.elasticsearch['index'])
            r = requests.post(Config.elasticsearch['uri_index'])
            print "...response from: %s (%s)" % (r.url, r.status_code)

        # check for mapping and create one if provided and does not already exist
        # this will automatically create the necessary index type if it is not already there
        if Config.elasticsearch['mapping']:
            r = requests.get(Config.elasticsearch['uri_records'] + '_mapping')
            if r.status_code == 404:
                print "Creating mapping for type: %s" % (Config.elasticsearch['type_record'])
                r = requests.put(Config.elasticsearch['uri_records'] + '_mapping', data=json.dumps(Config.elasticsearch['mapping']))
                print "...response from: %s (%s)" % (r.url, r.status_code)

                print "Creating mapping for type: %s" % (Config.elasticsearch['type_config'])
                r = requests.put(Config.elasticsearch['uri_configs'] + '_mapping', data=json.dumps(Config.elasticsearch['mapping']))
                print "...response from: %s (%s)" % (r.url, r.status_code)
        else:
            print "Warning: no elasticsearch mapping defined in Config.py."



    def generic_bibjsonify(self, bibjson):
        bibjson["url"] = Config.bibjson_url + bibjson["_id"]
        bibjson['_collection'] = [Config.bibjson_creator + '_____' + Config.bibjson_collname]
        bibjson['_created'] = datetime.now().strftime("%Y-%m-%d %H%M"),
        bibjson['_created_by'] = Config.bibjson_creator
        if "identifier" not in bibjson:
            bibjson["identifier"] = []

        #this line crashes Elastic Search? Check with Mark
        #CHANGE THE PARSER TO USE A LIST OF OBJECTS
        #Not making BibSoup IDs anymore
        #bibjson["identifier"].append({"type":"bibsoup", "id":bibjson["_id"], "url":bibjson["url"] })

        # set a date string
        y = bibjson.get('year',bibjson.get('journal',{}).get('year',False))
        if y:
            m = bibjson.get('month',bibjson.get('journal',{}).get('month','1'))
            if m.lower().startswith('jan'): m = '01'
            if m.lower().startswith('feb'): m = '02'
            if m.lower().startswith('mar'): m = '03'
            if m.lower().startswith('apr'): m = '04'
            if m.lower().startswith('may'): m = '05'
            if m.lower().startswith('jun'): m = '06'
            if m.lower().startswith('jul'): m = '07'
            if m.lower().startswith('aug'): m = '08'
            if m.lower().startswith('sep'): m = '09'
            if m.lower().startswith('oct'): m = '10'
            if m.lower().startswith('nov'): m = '11'
            if m.lower().startswith('dec'): m = '12'
            if len(m) == 1: m = '0' + m
            d = bibjson.get('day',bibjson.get('journal',{}).get('day','1'))
            if len(d) == 1: d = '0' + d
            bibjson['date'] = d + '/' + m + '/' + y
        
        return bibjson



    def get_bibserver_id(self, identifiers):
        if identifiers:
            terms = []
            for identifier in identifiers:
                terms.append({"term":{"identifier.canonical.exact": identifier["type"] + ":" + identifier["id"]}})
            q= {
              "query": {
                "bool": {
                  "should": terms
                }
              }
            }

            r = requests.get(Config.elasticsearch['uri_records'] + "_search", data=json.dumps(q))
            data = r.json()
            if data["hits"]["total"] > 0:
                #return existing id as specified in BibServer
                bibserver_id = data["hits"]["hits"][0]["_id"]
                #print "Found existing ID for %s: %s" % (identifiers, bibserver_id)
            else:
                #Create new id using UUID
                bibserver_id = uuid.uuid4().hex
                #print "Creating a new ID for %s: %s" % (identifiers, bibserver_id)
        else:
            #Create new id using UUID
            bibserver_id = uuid.uuid4().hex
            #print "Creating a new ID: %s" % (bibserver_id)
        return bibserver_id





# a wee class to thread the processes for the bulk importer
class Processes(threading.Thread):
    
    def run(self):
        while 1:
            fn = filejobs.get()
            p = Process(fn)
            p.process()
            filejobs.task_done()


# the process that the bulk importer (multiply) instantiates
class Process(ImporterAbstract):

    def __init__(self, filename, settings=Config.importer['load']['pubmedcentral'], options=[]):
        self.settings = settings # relevant configuration settings
        self.options = options # command-line options/arguments
        self.filename = filename
        self.procid = uuid.uuid4().hex
        if self.settings['skip_tar']:
            self.workdir = self.settings['workdir'] + os.listdir(self.settings['workdir'])[0] + '/'
        else:
            self.workdir = self.settings['workdir'] + self.procid + '/'
        self.b = Batch.Batch()
        self.m = MetadataReaders.MetadataReaderPMC()
        if not os.path.exists(self.settings['workdir']):
            try:
                os.makedirs(self.settings['workdir'])
            except:
                pass
        if not os.path.exists(self.workdir): os.makedirs(self.workdir)
        
    def process(self):
        print str(self.procid) + " processing " + self.filename

        # create folders in the workdir full of xml files to work on
        if not self.settings['skip_tar']:
            tar = tarfile.open(self.settings['filedir'] + self.filename)
            tar.extractall(path=self.workdir)
            tar.close()
            del tar

        pmcoaList = os.listdir(self.workdir) # list the folders in the workdir
        for fl in pmcoaList:
            files = os.listdir(self.workdir + fl)
            for f in files:
                # these may still contain files. If so, need to go down one more level
                if os.path.isdir(self.workdir + fl + '/' + f):
                    fcs = os.listdir(self.workdir + fl + '/' + f)
                    for fr in fcs: self._ingest(self.workdir + fl + '/' + f + '/' + fr)
                else:
                    self._ingest(self.workdir + fl + '/' + f)
        self.b.clear()
        if not self.settings['skip_tar']:
            shutil.rmtree(self.workdir) # delete the folder in the workdir that was used for this process

    # read in then delete the xml file
    # this causes delay and requires enough free memory to fit the file
    def _ingest(self, filepath):
        tree = ET.parse(filepath)
        elem = tree.getroot()
        doc = self.m(elem, nsprefix="")
        doc = doc.getMap()
        doc['_id'] = self.get_bibserver_id(False)
        doc = self.generic_bibjsonify(doc)
        self.b.add( doc )


# Bulk Importer class for PubMedCentral
# do a bulk import to instantiate an index from downloaded files rather than pulling from OAI feeds
class PMCBulkImporter(ImporterAbstract):

    def __init__(self, settings, options):
        self.settings = settings # relevant configuration settings
        self.options = options # command-line options/arguments

                
    # do everything
    def run(self):
        dirList = os.listdir(self.settings['filedir']) # list the contents of the directory where the source files are
        filecount = 0

        if self.settings['threads']:
            print "starting threaded processing"
            for x in xrange(self.settings['threads']):
                Processes().start()
            for i in dirList:
                filejobs.put(i)
            filejobs.join()

        else:
            for filename in dirList:
                filecount += 1
                if filecount >= self.settings['startingfile']: # skip ones already done by changing the > X
                    print filecount, self.settings['filedir'], filename
                    p = Process(filename, self.settings, self.options)
                    p.process()
        

# Generic Bulk Importer class for all sources
class BulkImporter(ImporterAbstract):

    def __init__(self, settings, options):
        self.settings = settings # relevant configuration settings
        self.options = options # command-line options/arguments

                
    # do everything
    def run(self):
        # Check that ElasticSearch is alive
        self.check_index()

        # If the user specified the --REBUILD flag, recreate the index
        if self.options['rebuild']:
            self.rebuild_index()

        # Now do the bulk importing. Choose an appropriate class based on the source.
        if self.options['source'] == "pubmedcentral":
            PMCBulkImporter(self.settings, self.options).run()
        elif self.options['source'] == "arxiv":
            ArXivBulkImporter(self.settings, self.options).run()
        else:
            print "Error: unhandled source ", self.options['source']



# Generic Bulk Importer class for all sources
class ArXivBulkImporter(ImporterAbstract):

    def __init__(self, settings, options):
        self.settings = settings # relevant configuration settings
        self.options = options # command-line options/arguments

        # We need to cast paths as absolute, not relative, as we change dir later
        self.current_dir = os.getcwd()
        self.filedir = self.current_dir + lstrip(self.settings['filedir'], '.')
        self.workdir = self.current_dir + lstrip(self.settings['workdir'], '.')

        self.contents_file = self.filedir + "arXiv_s3_downloads.txt"

        
        self.tmp_dir = self.workdir + "tmp/"
        self.extract_dir = self.workdir + "extract/"
        self.citation_dir = self.workdir + "citation/"
        self.extraction_queue = self.workdir + "arXiv_extraction_queue.txt"
        self.citation_queue = self.workdir + "arXiv_citation_queue.txt"

        self.s3_cmd_ex = self.current_dir + "/../ImportArxiv/tools/s3cmd/s3cmd" #TODO: Tidy this up

        if not os.path.exists(self.filedir):
            os.makedirs(self.filedir)

        if not os.path.exists(self.workdir):
            os.makedirs(self.workdir)

                
    # do everything
    def run(self):
    
        # First of all, download the arXiv source files.
        # Warning this is a lot of data and will cost $$$
        self.download()

        # Next, extract the archives
        self.extract()

        # Now, retrieve the citations
        self.retrieve_citations()


    def download(self):
        if not os.path.exists(self.contents_file):
            print "Error: arXiv contents file %s does not exist" % (self.contents_file)
            sys.exit(1)

        # Change directory to source folder
        os.chdir(self.filedir)

        print "Press 'x' to break after the current download."
        while True:
            arxiv_file_line = fq.get(self.contents_file)
            if arxiv_file_line == None: 
                break

            print "Processing ", arxiv_file_line
    
            return_code = call([self.s3_cmd_ex,'get','--add-header=x-amz-request-payer: requester','--skip-existing', arxiv_file_line])

            if return_code != 0:
                print "Error downloading", arxiv_file_line 
                break

            fq.pop(self.contents_file)
            # break if x was pressed
            if 'x' in nbRawInput('',timeout=1):
                print "Download suspended. Restart script to resume."
                break        

        # Change directory to project current folder
        os.chdir(self.current_dir)


    def extract(self):
        print "Press 'x' to interupt the extraction process"
        if not os.path.exists(self.tmp_dir):
            os.mkdir(self.tmp_dir)

        if not os.path.exists(self.extract_dir):
            os.mkdir(self.extract_dir)

        #Creates arXiv_extraction_queue.txt if it doesn't exist by finding all the tar files in the download folder
        if not os.path.exists(self.extraction_queue):
            call('find {source_dir}*.tar -type f > {target_file}'.format(
                    source_dir = self.filedir,
                    target_file = self.extraction_queue 
                    ) , shell = True)

        while True:
            file_name = fq.get(self.extraction_queue)
            if file_name is None: break

            print "Extracting bucket" , file_name
            if call(['tar','xf',file_name,'-C',self.tmp_dir]):
                # call returns 1 on error.
                break

            if call('find %s -name *.gz -type f -exec mv {} %s \;' % (self.tmp_dir, self.extract_dir), shell = True):
                break

            if call('rm -R ' + self.tmp_dir + '*', shell=True):
                break

            fq.pop(self.extraction_queue)

            # break if x was pressed
            if nbRawInput('',timeout=1) == 'x':
                print "Extraction suspended. Restart script to resume."
                break


    def retrieve_citations(self):
        if not os.path.exists(self.citation_dir):
            os.mkdir(self.citation_dir)

        if not os.path.exists(self.tmp_dir):
            os.mkdir(self.tmp_dir)

        #Creates arXiv_citationqueue.txt if it doesn't exist by finding all the gz files in the extract folder
        if not os.path.exists(self.citation_queue):
            call('find {source_dir}*.gz -type f > {target_file}'.format(
                    source_dir = self.extract_dir,
                    target_file = self.citation_queue 
                    ) , shell = True)

        while True:
            file_name = fq.get(self.citation_queue)
            if file_name is None: break
            
            arxiv_id = os.path.splitext(os.path.split(file_name)[1])[0]
            print "Retrieving citations", arxiv_id

            uncompressed_tmp = self.tmp_dir + arxiv_id
            if not os.path.exists(uncompressed_tmp):
                os.mkdir(uncompressed_tmp)
            returncode = call(["tar", "xzf", file_name, "-C", uncompressed_tmp])
            if (returncode == 1): #there was an error, so perhaps its not a Tar file. Instead try to decompress with plain old gunzip
                print "trying to gunzip instead for " + file_name
                os.system("gunzip -c %s > %s" % (file_name, uncompressed_tmp + "/file.tex"))

            #Now process .tex files
            for tex_file_name in os.listdir(uncompressed_tmp):
                if not (tex_file_name.endswith('.tex') or tex_file_name.endswith('.bbl')): continue
                self.settings["metadata_reader"].process(arxiv_id, uncompressed_tmp + '/' + tex_file_name)
                #call([self.tex2bibjson, "-a", arxiv_id, "-i", uncompressed_dir + "/" + tex_file_name, "-o", self.citations_dir + arxiv_id + "_" + tex_file_name + ".json"])


            if call('rm -R ' + uncompressed_tmp + '*', shell=True):
                break

            fq.pop(self.citation_queue)



# OAI-feed Importer class for ArXiv and for PubMedCentral
class OAIImporter(ImporterAbstract):

    def __init__(self, settings, options):
        self.settings = settings # relevant configuration settings
        self.options = options # command-line options/arguments
        self.es_uri_config = Config.elasticsearch['uri_configs'] + hashlib.md5(settings['uri']).hexdigest()
        

    def run(self):
        # Check that ElasticSearch is alive
        self.check_index()

        # If the user specified the --REBUILD flag, recreate the index
        if self.options['rebuild']:
            self.rebuild_index()

        # Connect to the repository
        registry = MetadataRegistry()
        registry.registerReader(self.settings["metadata_format"], self.settings["metadata_reader"])

        client = Client(self.settings["uri"], registry)
        identity = client.identify()

        print "Connected to repository: %s" % identity.repositoryName()

        # got to update granularity or we barf with: 
        # oaipmh.error.BadArgumentError: Max granularity is YYYY-MM-DD:2003-04-10T00:00:00Z
        client.updateGranularity()

        # Initialise some variables
        batcher = Batch.Batch()
        total_records = 0
        start = time.time()
        
        # Now do the synchonisation
        
        # If the user specified an identifier, then synchronise this record
        if (self.options['identifier'] is not None):
            total_records += self.synchronise_record(client, batcher, self.options['identifier'])
        else:
            # Else, synchronise using the date-range provided by the user, or failing that, 
            # the date-range based on the last sync

            # Get the synchronisation config record
            synchronisation_config = self.get_synchronisation_config()

            
            if self.options["from_date"] is not None:
                # If the user specified a from-date argument, use it
                from_date = self.options["from_date"] # already a date (not a datetime)
            elif synchronisation_config is not None and "to_date" in synchronisation_config:
                # Else read the last synchronised to_date from the config, and add on a day
                from_date = dateutil.parser.parse(synchronisation_config["to_date"]).date() + timedelta(days=1)
            else:
                # Else use the default_from_date in the config
                from_date = dateutil.parser.parse(self.settings['default_from_date']).date()

            if self.options["to_date"] is not None:
                to_date = self.options["to_date"] # already a date (not a datetime)
            else:
                to_date = (date.today() - timedelta(days=1))
            
            # Force the from_date to use time 00:00:00
            from_date = datetime.combine(from_date, _time(hour=0, minute=0, second=0, microsecond=0))

            # Force the to_date to use time 23:59:59
            to_date = datetime.combine(to_date, _time(hour=23, minute=59, second=59, microsecond=0))


            print "Synchronising from %s - %s" % (from_date, to_date)

            while from_date < to_date:
                next_date = datetime.combine(from_date.date() + timedelta(days=(self.settings['delta_days'] - 1)), _time(hour=23, minute=59, second=59, microsecond=0))
                number_of_records = self.synchronise_period(client, batcher, from_date, next_date)
                batcher.clear() #Store the records in elasticsearch
                self.put_synchronisation_config(from_date, next_date, number_of_records)
                from_date += timedelta(days=(self.settings['delta_days']))
                total_records += number_of_records

            
        # Store the records in the index
        batcher.clear()
        
        # Print out some statistics
        time_spent = time.time() - start
        print 'Total time spent: %d seconds' % (time_spent)

        if time_spent > 0.001: # careful as its not an integer
            print 'Total records synchronised: %i records (%d records/second)' % (total_records, (total_records/time_spent))
        else:
            print 'Total records synchronised: %i records' % (total_records)
        return total_records

        sys.exit()




    def synchronise_period(self, client, batcher, start_date, end_date):
        #print "Synchronising period: %s - %s" % (start_date, end_date)
        records = list(self.get_records_by_period(client, start_date, end_date))
        for record in records:
            batcher.add(self.bibify_record(record))
        return len(records)


    def synchronise_record(self, client, batcher, oaipmh_identifier):
        #print "Synchronising record: %s" % (oaipmh_identifier)
        record = self.get_record(client, oaipmh_identifier)
        if record is not None:
            batcher.add(self.bibify_record(record))
            return 1
        else:
            return 0


    def get_synchronisation_config(self):
        #print "Getting synchronisation_config for: %s" % (self.settings['uri'])
        r = requests.get(self.es_uri_config)
        if r.status_code == 404 or not r.json()["exists"]:
            print "Warning: No synchronisation_config found for %s" % (self.settings['uri'])
            return None
        else:
            return r.json()["_source"]


    def put_synchronisation_config(self, from_date, to_date, number_of_records):
        #print "Putting synchronisation_config for %s to %s" % (self.settings['uri'], self.es_uri_config)
        data = {'uri': self.settings['uri'], 'from_date': from_date.isoformat(), 'to_date': to_date.isoformat(), 'number_of_records': number_of_records}
        r = requests.put(self.es_uri_config, data=json.dumps(data))



    def get_records_by_period(self, client, start_date, end_date):
        print "Getting records for period: %s - %s" % (start_date, end_date)
        chunk_time = time.time()
        # print 'client.listRecords(from_=',start_date,'until=',end_date,'metadataPrefix=',self.settings["metadata_format"],'))'
        try:
            records = list(client.listRecords(
                from_          = start_date,  # yes, it is from_ not from
                until          = end_date,
                metadataPrefix = self.settings["metadata_format"]
                ))
        except NoRecordsMatchError:
            records = []

        d_time = time.time() - chunk_time
        print '...received %d records in %d seconds' % (len(records), d_time )
        chunk_time = time.time()
        return records



    def get_record(self, client, oaipmh_identifier):
        try:
            record = client.getRecord(
                identifier = oaipmh_identifier,
                metadataPrefix = self.settings["metadata_format"])
        except IdDoesNotExistError:
            print "Error: No record found for identifier: %s" % (oaipmh_identifier)
            record = None
        return record


    def bibify_record(self, record):
        header, metadata, about = record
        bibjson = metadata.getMap()
        bibjson["_oaipmh_datestamp"] = header.datestamp().isoformat()
        bibjson["_oaipmh_setSpec"] = header.setSpec()
        bibjson["_oaipmh_isDeleted"] = header.isDeleted()
        if "identifier" not in bibjson:
            bibjson["identifier"] = []
        bibjson["identifier"].append({"type": "oaipmh", "id": header.identifier(), "canonical": "oaipmh:" + header.identifier()})
        bibjson['_id'] = self.get_bibserver_id(bibjson["identifier"])
        bibjson = self.generic_bibjsonify(bibjson)
        return bibjson

