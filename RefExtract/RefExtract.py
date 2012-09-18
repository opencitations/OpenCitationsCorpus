#!/usr/bin/env python
#
# Automated reference extraction from gz package
#
#                        (CC BY-SA 3.0) 2012 Heinrich Hartmann
# 

DEBUG = 0

from RE_gz_extract  import gz_extract
from RE_tex_process import extract_bibitems, remove_tex_tags

def RefExtract(gz_path):
    ID = get_arxiv_id_from_path(gz_path)
    if DEBUG: print "# Processing ", ID

    # 1. Extract *.tex and *.bbl files from gz file
    tex_string  = gz_extract(gz_path)

    # 2. Extract bib_items
    bibitems    = extract_bibitems(tex_string)

    # 3. Strip remove tex-tags and write references to stdout
    out = ''
    for item in bibitems:
        out += ID + '|' + remove_tex_tags(item) + '\n'

    return out

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
    
    sys.stdout.write(RefExtract(gz_path))
    
    try:
        pass

    except:
        import sys, traceback
        type, value, tb = sys.exc_info()
        traceback.print_exc()
        pdb.post_mortem(tb)
