#!/usr/bin/env python
#
# Download ArXiv paper meeta data via OpenAccess API and store them into pickle files
#
# by Heinrich Hartmann, related-work.net,  2012
#
# Builds upon:
#
# (c) 2006 Rufus Pollock, GPL
# provided by infrae.com, available at http://www.infrae.com/download/oaipmh
#
# Description:
# * Meta information is downloaded in chunks of delta=1 moths
# * The arxiv meta repository starts with introduction of the new arxiv-id format in 2007.
#   However, older articles are contained in the 2007-05 month.
# * Arguments are parsed from the commandline. Only '--from' and '--to' are really important.
#

import oaipmh.client, oaipmh.metadata
import pickle, time, argparse, os
from datetime import date, datetime, timedelta

#
# Setup configuration
#

# Read command line arguments
arg_parser = argparse.ArgumentParser(description = 'Download metadata from Arxiv')
arg_parser.add_argument('--from', default = '2011-01-01', dest='from_date', 
                        help='enter from date in iso format,e.g. 2011-01-01')
arg_parser.add_argument('--to', default = '2011-01-05', dest='to_date',
                        help='enter end  date in iso format,e.g. 2011-01-05')
arg_parser.add_argument('--step', dest='delta', default = '1', type = int, 
                        help = 'number of months to querry at a time')
arg_parser.add_argument('--url', default = 'http://export.arxiv.org/oai2', 
                        help='URL of OA Server')
arg_parser.add_argument('--prefix', default = 'oai_dc', 
                        help='Metadata format format')
arg_parser.add_argument('--export-dir', default = '/home/web/Desktop/share/arxiv_meta/', dest = 'export',
                        help='Write files to this directory')

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
export_dir = args.export
if not os.path.exists(export_dir): 
    raise IOError('Directory not found')


# Print Status
print 'Harvesting data from %s in format %s'   % (url,metadataPrefix)
print 'Date Range   : %s -- %s in steps of %d' % (from_date.strftime('%Y-%m-%d'),until_date.strftime('%Y-%m-%d'),delta_months)
print 'Write Output : %s'                      % export_dir

#
# Main Program
#

def main():
    global client

    print '****** Starting Script ******' 

    client = oaipmh.client.Client(url)
    out = client.identify()

    print '****** Connected to repository: %s ******' % out.repositoryName()

    # got to update granularity or we barf with:
    # oaipmh.error.BadArgumentError: Max granularity is YYYY-MM-DD:2003-04-10T00:00:00Z
    client.updateGranularity()

    # Check if our data type is supported
    # check_formats(client,metadataPrefix)

    # register a reader on our client to handle oai_dc metadata
    # if we do not attempt to read records will fail with:
    #   .../oaipmh/metadata.py", line 37, in readMetadata
    #   KeyError: 'oai_dc'
    client.getMetadataRegistry().registerReader(
        metadataPrefix, 
        oaipmh.metadata.oai_dc_reader
        )

    start = time.time()
    for (c_date,n_date) in loop_months(from_date,until_date,delta_months):
        # get records
        try:
            records = list(get_records(c_date,n_date))
        except:
            print "failed recieving records!"
            continue
            
        # print_records(records, max_recs = 2)
        filename = export_dir + 'arixv_meta_%s_%s.pkl' % \
            (c_date.strftime('%Y-%m-%d'), n_date.strftime('%Y-%m-%d'))
        
        write_records(records, filename)

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

def check_formats(metadataPrefix):
    print '****** Available formats are: *****'
    # get a list of the metadata formats
    # returns a generator object with entries (format_name,description,None)

    format_gen = client.listMetadataFormats() 
    
    formats = [ f[0] for f in format_gen ]
    print formats

    # test if we have the format is supporrted
    if not metadataPrefix in formats: 
        raise ValueError("MetaPrefix %s not supported." % metadataPrefix)


def get_records(start_date,end_date):
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

def write_records(records, filename):
    print '***** Writing records to %s ********' % filename
    fh = open(filename,'wb')
    pickle.dump(records,fh)
    fh.close()

def print_records(records, max_recs = 5):
    print '****** Printing data ******'
    # for large collections this breaks
    count = 1

    for record in records:
        header, metadata, about = record
        map = metadata.getMap()
        print '****** Current record: %s' % header.identifier()
        for key, value in map.items():
            print '  ', key, ':', value
            
        if count > max_recs: break
        count += 1


if __name__ == '__main__':
    main()
