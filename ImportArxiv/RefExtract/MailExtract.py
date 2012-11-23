#!/usr/bin/env python
#
# Automated reference extraction from gz package
#
#                        (CC BY-SA 3.0) 2012 Heinrich Hartmann
# 

DEBUG = 0
import re
from RE_gz_extract  import gz_extract
from RE_tex_process import extract_bibitems, remove_tex_tags

def MailExtract(gz_path):
    ID = get_arxiv_id_from_path(gz_path)
    if DEBUG: print "# Processing ", ID

    # 1. Extract *.tex and *.bbl files from gz file
    tex_string  = gz_extract(gz_path)

    # Get rid of comments
    tex_string = remove_comments(tex_string)

    # 2. Find Email Addresses
    email_list = find_email_addresses(tex_string)

    # 3. Strip remove tex-tags and write references to stdout
    return ID + "|" + "|".join(email_list) + "\n"

def remove_comments(string, symbol = '%'):
    out = []
    for line in string.split('\n'):
        if symbol in line:
            line = line[:line.find(symbol)]
        out.append(line)
    return "\n".join(out)

email_re = re.compile(r'\b[\w\.-]+@[\w\.-]+\.\w{2,4}\b')
def find_email_addresses(string):
    # return uniquified email matches
    return list(set(email_re.findall(string)))


def parse_arguments():
    global DEBUG

    parser = argparse.ArgumentParser("Extract references from arXiv source *.gz files")
    parser.add_argument('gzfile', help = 'path to *.gz-file to process', type=str)
    parser.add_argument('-v','--verbose', help = 'Give detailed status information',type=int)
    
    args = parser.parse_args()
    if args.verbose:
        DEBUG = 1

    gz_path = args.gzfile
    if not os.path.isfile(gz_path):
        raise IOError('File not found: '+ gz_path)
    if not gz_path.endswith('.gz'):
        raise IOError('Not a gz-file: '+ gz_path)

    return gz_path

def get_arxiv_id_from_path(gz_path):
    '''
    Typical gz_path:
    * /media/buckets/Extracted/quant-ph0002087.gz
    * /media/buckets/Extracted/1001.1234.gz
    Returns:
    * quant-ph0002087
    * 1001.1234
    '''

    file_name = gz_path.split('/')[-1]
    return file_name[:-3]


if __name__ == '__main__':   
    import os, sys
    import argparse


    import ipdb as pdb
    BREAK = pdb.set_trace

    gz_path = parse_arguments()
    
    print MailExtract(gz_path)
    
    try:
        pass

    except:
        import sys, traceback
        type, value, tb = sys.exc_info()
        traceback.print_exc()
        pdb.post_mortem(tb)
