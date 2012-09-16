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

ref_file = 'arxiv_s3_buckets/reflist.txt'
meta_db = 'arxiv_meta_importer/meta_records_2.db'
match_file = 'matches.txt'

from unicodedata import normalize

import sqlite3 as lite
import sys,re
from collections import defaultdict
import time


def guess_arxiv_id(record):
    '''
    Finds arxiv ids in record - string, with some error tolerance
    returns id's without leading 'arxiv:' E.g.
    * 1234.5123
    * hep-th/1234567
    '''


    # Check for new syntax first:
    # Ex. arxiv:1023.1244, arxiv0213.1244, arXiv: 0123.4241, arXiv/ 1525.2144
    match = re.search(r'''
                arxiv           # matches (non case-sensitive)
                [:/]?            # : or maybe a slash / 
                [\s]?           # whitespace might be omitted
                (\d{4}\.\d{4})  # two four digit groups separated by '.'
                ''',record,re.IGNORECASE + re.VERBOSE)
        
    if match != None:
        # returns 1234.1234
        return match.group(1)
    

    # Check for arxiv url syntax
    # Eg. http://arxiv.org/abs/1023.1242  
    match = re.search(r'''
                 arxiv.org/abs/     # URL part
                 (\d{4}\.\d{4})     # ID part
                 ''', record, re.IGNORECASE + re.VERBOSE)

    if match != None:
        return match.group(1)
    
    
    # Check for old syntax:
    # math-ph/9902022 hep-th/9907167 arXiv:nucl-ex/0501009 arXiv:gr-qc/9910056  arXiv:astro-ph/0402529
    # arXiv:gr-qc/0010092
    # 
    # URLS are matched as well!
    # http://arxiv.org/abs/hep-th/9711162
    #
    # Step 1) isolate '/1234567' - part; remember 10 chars before that
    match = re.findall(r'(.{10})/(\d{7})', record )
    for prefix,number in match:
        for group_name in arxiv_group_names:
            if group_name in prefix:
                return group_name+'/'+number
            

    # Found nothing?
    return ''

# for use in the above function
arxiv_group_names = ['cond-mat', 'astro-ph', 'hep-ph', 'math', 'hep-th', 'quant-ph', 'gr-qc', 
                     'physics', 'nucl-th', 'hep-lat', 'hep-ex', 'cs', 'math', 'nlin', 'nucl-ex', 
                     'q-bio', 'chao-dyn', 'alg-geom', 'q-alg', 'cmp-lg', 'solv-int', 'dg-ga',
                     'patt-sol', 'funct-an', 'adap-org', 'mtrl-th', 'comp-gas', 'chem-ph', 'supr-con',
                     'atom-ph', 'acc-phys', 'plasm-ph', 'ao-sci', 'bayes-an' ] 


def guess_DOI():
    # NEED THIS
    #  Doi 10.1063/1.1749604 
    pass



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

    return 0


def guess_authors(record, author_dict):
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
    skip_authors = ['The'] # Lett, Bull.
    
    # generate a list of words = tokens of length >= 2
    tokens = re.findall(r'[A-Za-z]{2,}',record) 

    authors = []
    for t in tokens[:5]:
        # Starts with an upper case letter?
        if t[0].islower(): continue 
        
        # Author in skiplist?
        if t in skip_authors: continue

        # Author in db?
        if t in author_dict:
            authors.append(t)

    return authors
            




def TEST():
    from time import sleep
    fh = open(ref_file)
    counter = 0
    for line in fh:
        counter += 1
        if not counter % 300 == 14:  continue 
        ID, rec = line.split('|')
        ID = ID.strip('_')

        print rec[:-1]
        print "### ARXIV ID: %s ###" % guess_arxiv_id(rec)
        print "### YEAR: %d ####" % guess_year(rec)
        print "### AUTHORS: %s ###" % ' and '.join(guess_authors(rec))

        sleep(.1)

    fh.close()




def write_arxiv_id_matches(ref_file, match_file):
    wh = open(match_file,'w')
    fh = open(ref_file)
    counter = 0
    for line in fh:
        counter += 1

        ID, rec = line.split('|')
        ID = ID.strip('_')
        match = guess_arxiv_id(rec)
        
        if match != None:
#            print "found %s in %03d: %s" % (match.ljust(12), counter ,rec)
            wh.write('%s|%s\n' % (ID,match) )

    fh.close
    wh.close



def create_indices():

    # Initialize db
    con = lite.connect(db_file)

    # Write db scheme
    with con:
        cur = con.cursor()
        cur.execute("CREATE INDEX ayt_index ON meta(author,year,title)")
        cur.execute("")

#
# SQL CODE
# CREATE INDEX autor_index ON meta(autor)
# CREATE INDEX id_index ON meta(arxivid)
#
#




def main():
    # build lookup dicts
    author_recs = get_author_dict(max=10000000)
    author_nrec = dict( (n,len(rs)) for n,rs in author_recs.items() )
    title_tokens_n = get_title_tokens(max=10)
    # Cache those arrays with Pickle
    
    fh = open(ref_file)
    for line in fh:
        print line
        axiv_id,rec = line.split('|')

        tokens = get_tokens(rec)

        pred_authors = []
        for w in tokens[:4]:
            if w in author_nrec:
                pred_authors.append(w)

        print "Authors:", pred_authors

        tokens = map( lambda x: x.lower() , tokens )

        for p_author in pred_authors:
            for a_id in author_recs[p_author]:
                xid,xa,xt,xinf,xda,xsj = get_rec_by_arxiv_id(a_id)
                title_tokens = get_tokens(xt)
                hits = set(get_tokens(xt.lower())) & set(tokens)
                hit_ratio = len(hits) / float(len(get_tokens(xt))) * 100
                # weight by count of token 
                if hit_ratio > 70:
                    print "TOKEN MATCHING with", a_id, ": ", hit_ratio, "%" , hits 
                    print xt

        BREAK()

        # Get tokens
        # 
        # Check which Tokens are authors
        # 
        # Lookup corresponding titles
        # 
        # for each title
        #     check if words are contained in tokens
        #     if ratio good enough
        #        > print hit!

def get_tokens(string, lmin = 2):
    clean_rec = to_ascii(re.sub('[^A-Za-z\s]',' ',string))
    tokens = clean_rec.split()
    return filter(lambda x: len(x) > lmin, tokens )
    
def get_rec_by_arxiv_id(arxiv_id):
    con = lite.connect(meta_db)
    tokens = defaultdict(int)
    with con:
        cur = con.cursor()
        cur.execute("SELECT * FROM meta WHERE arxivid = '%s'" % arxiv_id)
        rec = cur.fetchone()

    return rec

def build_indices():
    global author_recs, author_nrec, title_tokens_n
    
    author_recs = get_author_dict(max=1000000)
    author_nrec = dict( (n,len(rs)) for n,rs in author_recs.items() )
    title_tokens_n = get_title_tokens(max=1000000)






def get_author_dict(max=1000):
    con = lite.connect(meta_db)

    authors = defaultdict(list)
    with con:
        cur = con.cursor()
        cur.execute("SELECT arxivid, autor FROM meta LIMIT %d" % max)
        
        for ID, a_string in cur.fetchall():
            for name in a_string.split(' and '):
                authors[name.split(',')[0]].append(ID)

    return authors


def get_title_tokens(max=1000):
    con = lite.connect(meta_db)

    tokens = defaultdict(int)
    with con:
        cur = con.cursor()
        cur.execute("SELECT titel FROM meta LIMIT %d" % max)
        
        for titels in cur.fetchall():
            titel = to_ascii(re.sub('[^A-Za-z\s]','',titels[0]))
            for token in titel.split():
                tokens[token] += 1

    return tokens


def to_ascii(string):
    try:
        out= normalize('NFKD', string).encode('ascii','ignore')
    except TypeError:
        out= string.encode('ascii','ignore')
    return out
    

if __name__ == '__main__':   
    DEBUG = 1
    import ipdb as pdb
    BREAK = pdb.set_trace

    try:
#        main()
        pass

    except:
        import sys,  traceback
        type, value, tb = sys.exc_info()
        traceback.print_exc()
        pdb.post_mortem(tb)







# def make_table( data, db_file, schema ):
#    make_table( author_recs.items(), match_db, 'author_id(author TEXT, arxiv_id TEXT)' )
#    make_table( author_nrec.items(), match_db, 'author_count(author TEXT, count INT)')
#     BREAK()
#     con = lite.connect(db_file)
#     with con:
#         table_name =  schema.split('(')[0]
#         cur = con.cursor()
#         cur.execute("DROP TABLE IF EXISTS " + table_name )
#         cur.execute("CREATE TABLE " + schema )
#         cur.executemany("INSERT INTO " + table_name + " VALUES(?, ?)", data )
