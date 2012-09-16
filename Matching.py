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
meta_db = 'arxiv_meta_importer/test.db'
match_file = 'matches_2.txt'

import sys,re, os, time, pickle

import sqlite3 as lite

from time import sleep
from collections import defaultdict
from unicodedata import normalize

def MATCH():
    DEBUG = 0
    global author_id_dict, token_count
    author_id_dict = get_author_id_dict(limit=1000000)
#    token_count = get_title_token_count_dict(limit = 100000)

    wh = open(match_file,'w')

    fh = open(ref_file)
    counter = 0
    match_counter = 0
    for line in fh:
        counter += 1
        if counter % 1000 == 0: 
            print "Processing line %10d - matched %10d" % ( counter , match_counter )
            wh.flush()

        ID, rec = line.split('|')
        ID = ID.strip('_')
        rec = rec.strip()  # get rid of \n at the end
        
        if DEBUG: print "### Matchig ", rec

        arxiv_id = guess_arxiv_id(rec)
        if not arxiv_id is None:
            if DEBUG: print "* found arxiv_id :", arxiv_id
            if DEBUG: print "* Matched:       :", get_meta_record_by_id(arxiv_id)[:3]
            match_counter += 1
            wh.write('%s:%s...|%s:%s...\n' % (ID.ljust(18),rec[:50],arxiv_id, '-'))
            continue

        year    = guess_year(rec)
        authors = guess_authors(rec)

        if (not year is None) and (not authors == []):
            if DEBUG: print "* year           :",year
            if DEBUG: print "* authors        :",authors

            if year < 1990:
                if DEBUG: print "* SKIPPED by year"
                continue

            main_author = authors[0]

            x_records=get_it_by_ay(main_author,year)
            if DEBUG: print "* matches in db  :", len(x_records)
            if DEBUG: print "* ratios         :", [ "%s...: %.3f" % (x_title[:10], match_p(x_title,rec)) for x_id, x_title in x_records]

            for x_id,x_title in x_records:
                if match_p(x_title,rec) > .7:
                    if DEBUG: print "* MATCHED        :", x_id, x_title
                    match_counter += 1
                    wh.write('%s:%s...|%s:%s...\n' % (ID.ljust(18),rec[:50],x_id.ljust(18),x_title[:50]))
                    if DEBUG: print 
                    break
            else: 
                # Sometimes not Title is given. Check for all authors, then?
                # e.g. C. Fuchs and H. H. Wolter, Eur. Phys. J. A  30 , 5 (2006).
                pass
                if DEBUG: print "* NO MATCH FOUND!"
        else:
            pass
            if DEBUG: print "* SKIPPED do not have year and author", year, authors
        
        if DEBUG: BREAK()
                    
    fh.close()
    wh.close()

re_token = re.compile(r'([A-Za-z]+)')
def match_p(s1,s2):
    # tokens lists
    t1 = re_token.findall(s1.lower())
    t2 = re_token.findall(s2.lower())

    if len(t1) == 0: return 0

    isec = set(t1) & set(t2)
    # print 'intersection',isec
    
    r1 = float(len(isec)) / len(t1)
    
    return r1


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
                [:/]?           # : or maybe a slash / 
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



def guess_authors(record):
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
        if t in author_id_dict:
            authors.append(t)

    return authors
            

def get_author_id_dict(limit=1000, cache = False):
    """
    Lookup dict: authorname --> [ arxiv id's ]
    """

    cache_file = "cache/author_id_dict_%d.pkl" % limit
    if cache and os.path.isfile(cache_file):
        print "loading cached vesion"
        fh = open(cache_file)
        out = pickle.load(fh)
        fh.close()
        return out

    con = lite.connect(meta_db)

    author_dict = defaultdict(list)
    with con:
        cur = con.cursor()
        cur.execute("SELECT arxiv_id, author FROM ayit_lookup LIMIT %d" % limit)
        for ID, name in cur.fetchall():
            author_dict[name].append(ID)

    if cache:
        print "writing cache"
        fh = open(cache_file,'w')
        pickle.dump(author_dict,fh)
        fh.close()

    return author_dict


def get_it_by_ay(author,year, delta=2):
    """
    Get all records from author in  [year - delta , year]
    """
    con = lite.connect(meta_db)

    recs = []
    with con:
        cur = con.cursor()
        cur.execute("SELECT arxiv_id, title FROM ayit_lookup WHERE author='%s' AND '%d' <= year AND year <= '%d' " % (author,year-delta,year))
        recs = [ (to_ascii(x_id), to_ascii(x_title)) for x_id,x_title in cur.fetchall()]

    return recs



def get_title_token_count_dict(limit=1000):
    """
    Count occurence of tokens = words in titles
    """
    token_count = defaultdict(int)

    con = lite.connect(meta_db)
    with con:
        cur = con.cursor()
        cur.execute("SELECT title FROM meta LIMIT %d" % limit)
        
        for title in cur.fetchall():
            for token in re.findall(r'([A-Za-z]+)',title[0]):
                token_count[token.lower()] += 1

    return token_count


def get_meta_record_by_id(arxiv_id):
    con = lite.connect(meta_db)
    tokens = defaultdict(int)
    with con:
        cur = con.cursor()
        cur.execute("SELECT * FROM meta WHERE arxiv_id = '%s'" % arxiv_id)
        rec = cur.fetchone()
    return rec
    


def create_indices():
    con = lite.connect(meta_db)
    with con:
        cur = con.cursor()
        cur.execute("CREATE INDEX ay_index  ON ayit_lookup(author,year)")
        cur.execute("CREATE INDEX arxiv_id  ON meta(arxiv_id,title)")




############## DEPRECATED #############################



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
    




def get_dicts():
    global author_recs, author_nrec, title_tokens_n
    
    author_recs = get_author_dict(max=1000000)
    author_nrec = dict( (n,len(rs)) for n,rs in author_recs.items() )
    title_tokens_n = get_title_tokens(max=1000000)




def get_title_token_count(limit=1000):
    con = lite.connect(meta_db)

    tokens = defaultdict(int)
    with con:
        cur = con.cursor()
        cur.execute("SELECT titel FROM meta LIMIT %d" % limit)
        
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
        MATCH()
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
