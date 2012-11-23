#
# Pubmed Central meta and reference extraction
#
# 2012 by Heinrich Hartmann
#
# License: Creative-Commons Share-Alike
# 
# This work is part of related-work.net
#

"""This script provides functions to process articles from the PUB MED
CENTRAL ftp-server.

ftp://ftp.ncbi.nlm.nih.gov/pub/pmc/articles.A-B.tar.gz
ftp://ftp.ncbi.nlm.nih.gov/pub/pmc/articles.C-H.tar.gz 
ftp://ftp.ncbi.nlm.nih.gov/pub/pmc/articles.I-N.tar.gz 
ftp://ftp.ncbi.nlm.nih.gov/pub/pmc/articles.O-Z.tar.gz

These contain xml files in the format described in
* http://dtd.nlm.nih.gov/archiving/3.0/archivearticle3.dtd
* http://dtd.nlm.nih.gov/archiving/tag-library/3.0/index.html

Output formats:
* Metadata 
  is exported as dictionary with keys:
  - title    : string          e.g. 'EU 2.0'
  - authors  : list of strings e.g. ['Merkel, Angela', 'Steinbrueck, Peer']
  - abstract : string          e.g. 'bla bla bla' 
  - year     : string          e.g. '2012'
  - ids      : dict of string  e.g. {'doi': '1235', 'pmc': '135321', 'pmid': '125123'}
  - journal  : string          e.g. 'J GER SOC BLA'
 
  This data is exported as an  UTF-8 encoded json string

* References 
  are exported as table rows of the form
  '{source_id}|{ref_string}|{target_ids}',
  where
  * source_id  is the pmid of paper being processed,
  * target_ids is a list of found ids, separated by '; ' 
    valid ids types are: pmc, pmid, doi, ...
  * ref_string is a short summary of the cited source. The format is roughly:
    '{authors}, {title}, {journal} ({year})'

* Gather statistics:
  * Translation table pubmed-id:pmc-id

"""

#
# Imports
#

# Essential classes
from xmlparsers import Paper, Reference
from tarfile import open as tar_open


# Logging and monitoring
from monitor import MonitorThread
from collections import defaultdict
STATUS = defaultdict(int)
Monitor = MonitorThread(STATUS)

import logging
logging.basicConfig(level=logging.INFO)

# Debugging
import ipdb
BREAK = ipdb.set_trace

from pprint import pprint as PRINT
from lxml import etree
def XPRINT(xml):
    print etree.tostring(xml,pretty_print = True)
    return


#
# Global Variables
#

# Input data
source_files = [
    'pubmed_ftp/articles.A-B.tar.gz',
    'pubmed_ftp/articles.C-H.tar.gz',
    'pubmed_ftp/articles.I-N.tar.gz',
    'pubmed_ftp/articles.O-Z.tar.gz'
    ]

# Write output to
meta_json_filename = 'meta.json.txt'
reference_filename = 'references.txt'
id_table_filename  = 'pmid_table.txt'


#
# Control flows
#

def main():
    Monitor.start()
    # inspect_records()
    write_id_table()
    pmc_lookup=get_pmid_dict()
    write_references(pmc_lookup)
    Monitor.end()
    #BREAK()
    return


def write_references(pmc_lookup):
    """
    Prints citation graph to stdout. Format:
    pmc-source | ref-string | pmc-target
    """
    global STATUS

    fh = open(reference_filename,'w')

    for path, paper in get_paper(*source_files):
        STATUS['paper_count'] += 1
        if not 'pmc' in paper.ids:
            STATUS['source_id_fail'] += 1
            continue

        source_id = paper.ids['pmc']
        for reference in paper.get_references():
            STATUS['reference_count'] += 1
            target_id = None

            if 'pmc' in reference.ids:
                # does not appear to happen
                target_id = reference.ids['pmc']
                STATUS['pmc_found'] += 1
            elif 'pmid' in reference.ids:
                # translate to pmc using lookup dict
                try:
                    target_id = pmc_lookup[reference.ids['pmid']]
                    STATUS['pmc_lookup'] += 1
                except KeyError:
                    # If pmid is not found, target_id remains None.
                    pass

            # Add further lookup strategies here. E.g. doi / string matching
            if not target_id:
                continue

            STATUS['matches'] += 1
            fh.write("{source_id}|{reference}|{target_id}\n".format(**locals()))

    fh.close()

def get_pmid_dict():
    """
    Create lookup dict for pmc'ids. 
    (cf. http://www.ncbi.nlm.nih.gov/pmc/pmctopmid/)
    Requires id_table_file to be filled by write_id_table.

    >>> pmc = get_pmid_dict()
    >>> pmc['19255307'] = '2738645'
    asserts that pmid '19255307' corresponds to pmc '2738645'
    """
    fh = open(id_table_filename)
    pmid_dict = {}

    for line in fh:
        record = line.split('|')
        pmid_dict[record[1]]=record[0]

    # Remark: The first line schould contain the table schema:
    # 'pmc|pmid|doi|pii|publisher-id|manuscript|coden|other'
    # hence pmid_dict['pmid'] = 'pmc'

    return pmid_dict


def write_id_table():
    """
    Write id information for all papers into id_table_file.
    The first line describes the schema:
    'pmc|pmid|doi|...'
    """

    # used for status reporting in monitor thread
    global STATUS

    id_types = ['pmc','pmid', 'doi', 'pii', 'publisher-id', 'manuscript', 'coden', 'other' ]
    STATUS['paper_count'] = 0
    out = open(id_table_filename,'w')

    # first lines contains schema
    out.write("|".join(id_types) + '\n')
    for path, paper in get_paper(*source_files):
        STATUS['paper_count'] += 1
        ids = defaultdict(str,paper.ids)
        out.write(u"|".join([ ids[id_type].replace('|',"") for id_type in id_types ]).replace('\n','').encode('UTF-8')+"\n")

    out.close()


def inspect_records():
    """
    Convenience function to inpect data
    """
    for path, paper in get_paper(*source_files):
        print "="*80
        PRINT( paper.meta )
        print "="*40
        for reference in paper.get_references():
            PRINT( reference.meta )
            if (reference.ids == {} and not reference.type == 'other' ):
                XPRINT(reference.xml)
                BREAK()


#
# Iteration through source files
#

def get_paper(*source_files):
    """ 
    Walks through all *.nxml files contained in tar archives passed as
    file names, and returns them as tuple
    (path, paper)
    where:
    * path is the path of the nxml-file inside the tar file 
    * paper is an paper_record object containing the contents of the nxml-file
    """

    for file_name in source_files:
        logging.info('Processing bucket %s' % file_name )

        fh = tar_open(file_name)
        # raises IO error if file not found

        for file_info in fh:
            # filter *.nxml files
            if file_info.isdir() or not file_info.name.endswith('.nxml'):
                continue
            
            path = file_info.name

            try:
                paper = Paper(fh.extractfile(file_info))
            except SyntaxError as err:
                logging.warning("{0} in {1}".format(err,path))
            yield  path, paper
        fh.close()


#
# Call main function
#


if __name__ == '__main__':
    main()
