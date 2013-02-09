#!/usr/bin/env python
# encoding: utf-8

import sys
import getopt

from oaipmh.client import Client
from oaipmh.metadata import MetadataRegistry, oai_dc_reader


help_message = '''
The help message goes here.
'''

URL = 'http://export.arxiv.org/oai2'


#import oaipmh.client, oaipmh.metadata
#import pickle, time, argparse, os
#from datetime import date, datetime, timedelta

import time, argparse, os
from datetime import date, datetime, timedelta

# Setup configuration
#

# Read command line arguments
arg_parser = argparse.ArgumentParser(description = 'Download metadata from Arxiv')
arg_parser.add_argument('--from', default = '2012-01-02', dest='from_date', 
                        help='enter from date in iso format,e.g. 2012-01-02')
arg_parser.add_argument('--to', default = '2012-01-03', dest='to_date',
                        help='enter end  date in iso format,e.g. 2012-01-03')
arg_parser.add_argument('--step', dest='delta', default = '1', type = int, 
                        help = 'number of months to querry at a time')
arg_parser.add_argument('--url', default = 'http://export.arxiv.org/oai2', 
                        help='URL of OA Server')
arg_parser.add_argument('--prefix', default = 'oai_dc', 
                        help='Metadata format format')
#arg_parser.add_argument('--export-dir', default = pkl_dir, dest = 'export',
#                        help='Write files to this directory')

args = arg_parser.parse_args()

# Set global variables
# Arxiv oa server:
url = args.url
metadataPrefix = args.prefix

# Get records in time range in chunks of .. months
from_date    = datetime.strptime(args.from_date, "%Y-%m-%d")
until_date   = datetime.strptime(args.to_date,   "%Y-%m-%d")
delta_months = args.delta

# Export to directory
#export_dir = args.export
#if not os.path.exists(export_dir): 
#    print "Creating %s" % export_dir
#    os.makedirs(export_dir)


# Print Status
os.system('clear')
print "MetaData Importer"
print 'Harvesting data from %s in format %s'   % (url,metadataPrefix)
print 'Date Range   : %s -- %s in steps of %d' % (from_date.strftime('%Y-%m-%d'),until_date.strftime('%Y-%m-%d'),delta_months)
#print 'Write Output : %s'                      % export_dir










class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg

def connect():
    print "Connecting to: %s" % URL
    registry = MetadataRegistry()
    registry.registerReader('oai_dc', oai_dc_reader)
    client = Client(URL, registry)
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
    client.getMetadataRegistry().registerReader(metadataPrefix, oai_dc_reader)
    
    #for record in client.listRecords(metadataPrefix='oai_dc'):
    #   print record
    
    start = time.time()
    for (c_date,n_date) in loop_months(from_date,until_date,delta_months):
        records = list(get_records(client, c_date, n_date))
        # get records
        #try:
        #    records = list(get_records(c_date,n_date))
        #except:
        #    print "failed receiving records! %s" % msg
        #    continue
            
        # print_records(records, max_recs = 2)
        #filename = export_dir + 'arixv_meta_%s_%s.pkl' % \
        #    (c_date.strftime('%Y-%m-%d'), n_date.strftime('%Y-%m-%d'))
        
        print_records(records)

    print 'Total Time spent: %d seconds' % (time.time() - start)


def loop_months(start_date, end_date, month_step=1):
    if month_step == 0: return

    current_date = start_date
    while True:
        if month_step > 0 and current_date >= end_date: break
        if month_step < 0 and current_date <= end_date: break
    
        carry, new_month = divmod(current_date.month - 1 + month_step, 12)
        new_month += 1
        next_date = current_date.replace(year=current_date.year + carry, month=new_month)
        
        if month_step > 0 and next_date > end_date: next_date = end_date
        if month_step < 0 and next_date < end_date: next_date = end_date

        if month_step > 0: 
            yield current_date,next_date
        if month_step < 0: 
            yield next_date, current_date

        current_date = next_date


def get_records(client, start_date, end_date):
    print '****** Getting records ******'
    print 'from   : %s' % start_date.strftime('%Y-%m-%d')
    print 'until  : %s' % end_date.strftime('%Y-%m-%d')

    chunk_time = time.time()

    print 'client.listRecords(from_=',start_date,'until=',end_date,'metadataPrefix=',metadataPrefix,'))'
    records = list(client.listRecords(
            from_          = start_date,  # yes, it is from_ not from
            until          = end_date,
            metadataPrefix = metadataPrefix
            ))

    d_time = time.time() - chunk_time
    print 'recieved %d records in %d seconds' % (len(records), d_time )
    chunk_time = time.time()

    return records


def print_records(records, max_recs = 2):
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

def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        try:
            opts, args = getopt.getopt(argv[1:], "ho:v", ["help", "output="])
        except getopt.error, msg:
            raise Usage(msg)
    
        # option processing
        for option, value in opts:
            if option == "-v":
                verbose = True
            if option in ("-h", "--help"):
                raise Usage(help_message)
            if option in ("-o", "--output"):
                output = value
        

        connect()
    
    except Usage, err:
        print >> sys.stderr, sys.argv[0].split("/")[-1] + ": " + str(err.msg)
        print >> sys.stderr, "\t for help use --help"
        return 2


if __name__ == "__main__":
    sys.exit(main())
