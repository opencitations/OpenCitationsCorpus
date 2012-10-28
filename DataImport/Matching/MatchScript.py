#!/usr/bin/env python
#
# Executable version of Match.py
#

from Match import Match
from multiprocessing import Pool
import argparse, sys, os, re

sys.path.append('../tools')
from shared import yield_lines_from_dir, yield_lines_from_file

DEBUG = 0
LOG = sys.stderr

def main():
    global DEBUG
    # 
    # Parse commandline arguments
    #
    
    # Setup Parser
    parser = argparse.ArgumentParser()
    parser.add_argument('reffile', nargs='?', help = 'path to text file/text dir containing references', type=str)
    parser.add_argument('--stream', help = 'read input from stdin', action="store_true", default=False)
    parser.add_argument('-m', help = 'number of parallel processes', type=int, default=1)
    parser.add_argument('-v','--verbose', help = 'Give detailed status information',type=int)

    args = parser.parse_args()
    if args.verbose:
        DEBUG = 1

    ref_file = args.reffile
    num_proc = args.m
    print num_proc

    #
    # Execute program
    #

    # Get input line iterator from different sources
    if args.stream:
        in_iter = sys.stdin
    elif os.path.isfile(ref_file):
        in_iter = yield_lines_from_file(ref_file)
    elif os.path.isdir(ref_file):
        in_iter = yield_lines_from_dir(ref_file,'.txt')
    else:
        raise IOError('File not found: '+ ref_file)


    if num_proc >= 1:
        p=Pool(num_proc)
        out_iter = p.imap_unordered(get_match,in_iter,chunksize=100)
    else:
        out_iter = get_match(in_iter)

    for i, line in enumerate(out_iter):
        if i % 100 == 0:
            LOG.write( 'Matching line %d \n' % i )
        print line
    


def get_match(line):
    # Example record:
    # line = '1001.0056|K. Behrend [ .... ] .  128 (1997), 45--88.\n'
    ID, rec = line.split('|')[:2]

    # cleanup
    rec = rec.strip()
    ID = repair_arxiv_id(ID)

    # Match
    match = Match(rec)
            
    if match:
        return  ID + "|" + rec + "|" + match
    else:
        return  ID + "|" + rec + "|"
    

def repair_arxiv_id(arxiv_id):
    """
    Reinserts '/' in old arxiv id's

    Examples:
    >>> repair_arxiv_id('math-ph1234567') 
    'math-ph/1234567'

    >>> repair_arxiv_id('1024.1242')
    '1026.1242'
    """

    # initialize compiled regexp as static variable = attribute
    if not 'regexp' in dir(repair_arxiv_id):
        repair_arxiv_id.regexp = re.compile(r'([a-zA-Z-]{2,9})(\d{7})')
        
    m = repair_arxiv_id.regexp.match(arxiv_id)
    if m:
        return m.group(1) + '/' + m.group(2)
    else:
        return arxiv_id


if __name__ == '__main__':
    main()
