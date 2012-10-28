#!/usr/bin/env python
#
# Matching reference entries against our meta_database
#
#
# Example Records:
# * N. Nisan and A. Wigderson.  Hardness vs randomness.  em Journal of Computer and System Sciences , 49:149--167, 1994.
# * A. Pavan.  Comparison of reductions and completeness notions.  em SIGACT News , 34(2):27--41, June 2003.
# * J. Lawrence, M. Ashley, A. Tokovinin, T. Travouillon, Exceptional astronomical seeing conditions above Dome C in Antarctica , Nature , 431 , pp. 278-281, 2004.
# * F. Abe em et al. (The CDF Collaboration), Phys. Rev. D  54 , 735 (1996).
# * B. Abbott em et al. (The D0 Collaboration), Phys. Rev. Lett.  82 , 4975 (1999).
# * et al.(1999) Reimers , Hagen , Hopp reimersetal99-1 Reimers , D., Hagen , H. J., Hopp , U., 1999, A A, 343, 157
# * et al.(2008) Rubin , Williams , Bolte , Koester rubinetal08-1 Rubin , K. H. R., Williams , K. A., Bolte , M., Koester , D., 2008, AJ, 135, 2163
# * et al.(2009) Salaris , Serenelli , Weiss , Miller Bertolami salarisetal09-1 Salaris , M., Serenelli , A., Weiss , A., Miller Bertolami , M., 2009, ApJ, 692, 1013
# * S. Typel, Phys. Rev. C  71 , 064301 (2005).
# * H. R. Jaqaman, Phys. Rev. C  38 , 1418 (1988).
# * H. Takemoto, it et al. , Phys. Rev. C  69 , 035802 (2004).
# * V. Baran, it et al. , Phys. Rept.  410 , 335 (2005).
#

import sys,re, os, time, pickle
import sqlite3 as lite
from time import sleep
from collections import defaultdict
from unicodedata import normalize

# Akward shared import
sys.path.append('../tools')
from shared import to_ascii

# Init global variables
DEBUG = 0
meta_db = '../DATA/META/arxiv_meta.db'


#
# Matching algorithm
#

def Match(rec):
    """
    Matches contenst of rec-string against metadatabase. 
    * If a match is found the arxiv-id is returned
    * If not, None is returned

    Example:
    >>> Match("Hartmann, Period and Mirror Maps for the Quartic K3, 2011")
    '1101.4601'
    >>> Match("Harxamn, XXX, 1911")
    None
    
    Remark:
    * The fist call initializes a author lookup table which takes a few seconds to load.
    """
    if DEBUG: print "### Matchig ", rec
    if not 'author_dict' in dir(Match):
        Match.author_dict = get_author_count_dict(limit = -1)
    
    # 1. Try to find an arxiv id in rec-string.
    arxiv_id = guess_arxiv_id(rec)
    if arxiv_id:
        if DEBUG: print "* found arxiv_id :", arxiv_id
        if DEBUG: print "* Matched:       :", ', '.join(get_meta_record_by_id(arxiv_id)[:3])
        return arxiv_id

    # 2. Try to get author name and year
    year    = guess_year(rec)
    authors = guess_authors(rec, limit = 1)

    if (year is None) or (authors == []):
        if DEBUG: print "* SKIPPED do not have year (%s) and author (%s)" % (year, ', '.join(authors))
        return

    # found author and year both?
    if DEBUG: print "* year           :",year
    if DEBUG: print "* authors        :",authors

    if year < 1990:
        if DEBUG: print "* SKIPPED by year"
        # Remark: The arxiv exisits since 1991
        return

    main_author = authors[0]

    # Lookup papers in db:
    x_records=get_it_by_ay(main_author,year)

    if DEBUG: print "* matches in db  :", len(x_records)
    if DEBUG: print "* ratios         :", [ "%s...: %.3f" % (x_title[:10], match_p(x_title,rec)) for x_id, x_title in x_records]

    for x_id,x_title in x_records:
        # Is x_title and rec similar? Test using match_p
        if match_p(x_title,rec) > .7:
            if DEBUG: print "* MATCHED        :", x_id, x_title, "\n"
            return x_id

    # No match found, yet:
    # Sometimes not Title is given. Check for all authors, then?
    # e.g. C. Fuchs and H. H. Wolter, Eur. Phys. J. A  30 , 5 (2006).
    if DEBUG: print "* NO MATCH FOUND!"


def match_p(s1,s2):
    # tokens lists
    t1 = re_token.findall(s1.lower())
    t2 = re_token.findall(s2.lower())

    if len(t1) == 0: return 0

    isec = set(t1) & set(t2)
    # print 'intersection',isec
    
    r1 = float(len(isec)) / len(t1)
    
    return r1
re_token = re.compile(r'([A-Za-z]+)')


#
# Guessing subroutines
#

def guess_arxiv_id(record):
    '''
    Finds arxiv ids in record string, with some error tolerance
    returns id's without leading 'arxiv:' E.g.
    * 1234.5123
    * hep-th/1234567
    '''

    # Check for new syntax first:
    # Ex. arxiv:1023.1244, arxiv0213.1244, arXiv: 0123.4241, arXiv/ 1525.2144
    # Mixed versions: arXiv:math/0705.1653.
    match = re.search(r'''
                arxiv           # matches (non case-sensitive)
                [:/\s]?         # : or maybe a slash / 
                [a-z-]{0,9}     # leave room for wrongly put group definition
                [/\s]?          # whitespace might be omitted
                (\d{4}\.\d{4})  # two four digit groups separated by '.'
                ''',record,re.IGNORECASE + re.VERBOSE)
        

    if not match is None:
        # returns 1234.1234
        return match.group(1)
    

    # Check for arxiv url syntax
    # Eg. http://arxiv.org/abs/1023.1242  
    match = re.search(r'''
                 arxiv.org/abs/     # URL part
                 (\d{4}\.\d{4})     # ID part
                 ''', record, re.IGNORECASE + re.VERBOSE)

    if not match is None:
        return match.group(1)
    
    
    # Check for old syntax:
    # math-ph/9902022 hep-th/9907167 arXiv:nucl-ex/0501009 arXiv:gr-qc/9910056  arXiv:astro-ph/0402529
    # arXiv:gr-qc/0010092
    # 
    # URLS are matched as well!
    # http://arxiv.org/abs/hep-th/9711162
    #
    # Step 1) isolate '/1234567'-part; remember 10-chars x before that
    # Step 2) check if x contains a valid arxiv group name
    match = re.findall(r'(.{10})/(\d{7})', record )
    for prefix,number in match:
        for group_name in arxiv_group_names:
            if group_name in prefix:
                return group_name+'/'+number
 
            


# for use in the above function, Arxiv groups sorted by number of submissions
arxiv_group_names = ['cond-mat', 'astro-ph', 'hep-ph', 'math', 'hep-th', 'quant-ph', 'gr-qc', 
                     'physics', 'nucl-th', 'hep-lat', 'hep-ex', 'cs', 'math', 'nlin', 'nucl-ex', 
                     'q-bio', 'chao-dyn', 'alg-geom', 'q-alg', 'cmp-lg', 'solv-int', 'dg-ga',
                     'patt-sol', 'funct-an', 'adap-org', 'mtrl-th', 'comp-gas', 'chem-ph', 'supr-con',
                     'atom-ph', 'acc-phys', 'plasm-ph', 'ao-sci', 'bayes-an' ] 



def guess_year(record):
    """
    Extracts year from record: 
    * Matches the last occurence (yyyy)
    * Matches the last occurence if yyyy
    * checks if 1800 <= yyyy <= 2020
    * Returns 0 if nothing found
    """

    # Try first with '(' ')'
    matches = re.findall(r'[(] (\d\d\d\d) [)]',record,re.VERBOSE)

    for m in matches[::-1]: # start from the end!
        y = int(m)
        if 1800 <= y and y <= 2050:
            return y

    matches = re.findall(r'(\d\d\d\d)',record,re.VERBOSE)
    for m in matches[::-1]: # start from the end!
        y = int(m)
        if 1800 <= y and y <= 2020:
            return y



def guess_authors(record, limit = 5):
    """
    Finds author name in record, using the following heuristics:
    * Author comes first in record (search in first 5 tokens)
    * two or more letters long
    * starts with a capital letter 
    * Author occures in Author database (!) (needs author_dict to be set)

    To be implements:
    * If 'and' is present then before and afterwards comes probably and author
    * If 'et al' is present, then the authors are probably before that
    """
    
    # Exclude some odd author names in db
    skip_authors = ['The'] # 'Lett', 'Bull.'
    
    
    # generate a list of words = tokens of length >= 2
    tokens = re.findall(r'[A-Za-z]{2,}',record)

    authors = []
    for t in tokens[:5]:
        # Starts with an upper case letter?
        if t[0].islower(): continue
        
        # Author in skiplist?
        if t in skip_authors: continue

        # Author in db?
        if t in Match.author_dict:
            authors.append(t)

            if len(authors) == limit:
                return authors

    return authors
 
           
def guess_DOI():
    # NEED THIS
    #  Doi 10.1063/1.1749604 
    pass


#
# Database querries
#

def get_meta_record_by_id(arxiv_id):
    """
    Lookup arxiv_id in meta_db
    """

    con = lite.connect(meta_db)
    tokens = defaultdict(int)
    with con:
        cur = con.cursor()
        cur.execute("SELECT * FROM meta WHERE arxiv_id = '%s'" % arxiv_id)
        rec = cur.fetchone()
    return rec    


def get_it_by_ay(author,year, delta=2):
    """
    Get arxiv_id (i) and title (t) of all papers from author (a) in in year (y) + [-delta..0]
    """
    con = lite.connect(meta_db)

    recs = []
    with con:
        cur = con.cursor()
        cur.execute("SELECT arxiv_id, title FROM ayit_lookup WHERE author='%s' AND '%d' <= year AND year <= '%d' " % (author,year-delta,year))
        recs = [ (to_ascii(x_id), to_ascii(x_title)) for x_id,x_title in cur.fetchall()]
    return recs


def get_author_count_dict(limit=1000):
    """
    Count number of paper by authors
    """
    author_count = defaultdict(int)

    con = lite.connect(meta_db)
    with con:
        cur = con.cursor()
        cur.execute("SELECT author FROM ayit_lookup LIMIT %d" % limit)
        
        for author in cur.fetchall():
            author_count[to_ascii(author[0])] += 1

    return author_count


