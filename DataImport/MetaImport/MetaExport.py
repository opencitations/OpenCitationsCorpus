#
# Takes pickled oa-metadata entries lying in a folder and writes writes them to:
#
# 1. Print records in format to the console in the format:
#    id | authors | title | comments | date | subject
#
#    Example: 
#    1010.5365|Melnikov, ...|Heterotic Si... |JHEP 1109:065,2011, doi:10.1007/JHEP09(2011)065|2010-10-26|High Energy Physics - Theory
#
# 2. Stores metadata in an sqlite table with schema:
#
#    meta(arxivid TEXT, autor TEXT, titel TEXT, info TEXT, date TEXT, subject TEXT, year INT)
#
#    We append year as an int field to allow the creation of efficient searching
#
# 3. Stores another list in an s1lite table with schema:
#
#    ayit_lookup(author TEXT, year INT, arxiv_id TEXT, title TEXT)
#
#
 
import sys, os, pickle, re
import sqlite3 as lite
from MetaRead import get_meta_from_pkl

# Akward tools import
sys.path.append('../tools')
from shared import to_ascii, group_generator

pkl_dir       = '../DATA/META/PKL/'
db_file       = '../DATA/META/arxiv_meta.db'

def main():
    print "Writing", db_file
    # print_records()
    print "Writing meta table"
    fill_meta_table(db_file,pkl_dir)
    print "Writing author lookup table"
    fill_author_table(db_file,pkl_dir)
    pass


def print_records(pkl_dir=pkl_dir):
    for rec_id, meta_dict in get_meta_from_pkl(pkl_dir):
        authors = ' and '.join(meta_dict['creator'])
        title   = meta_dict['title'][0]
        info    = ', '.join(meta_dict['identifier'][1:])
        date    = meta_dict['date'][0] 
        subject = ', '.join(meta_dict['subject'])
        year    = date[0:4]
        print "|".join([rec_id, authors, title, info, date, subject, year])


def fill_meta_table(db_file, pkl_dir = pkl_dir, max_batch = -1):
    """ 
    Creates a table meta in db_file and inserts records from pkl_files in pkl_dir
    Schema: arxiv_id, author, title, abstract, info, subject, year
    """

    # Initialize db
    con = lite.connect(db_file)

    # Create/Reset table
    with con:
        cur = con.cursor()
        cur.execute("DROP TABLE IF EXISTS meta")
        cur.execute("CREATE TABLE meta(arxiv_id TEXT, author TEXT, title TEXT, abstract TXT, info TEXT, subject TEXT, year INT)")


    def prepare_meta_row(rec_id,meta_dict):
        authors  = ' and '.join(meta_dict['creator'])
        title    = meta_dict['title'][0]
        abstract = meta_dict['description'][0]
        info     = ', '.join(meta_dict['identifier'][1:])
        date     = meta_dict['date'][0] 
        subject  = ', '.join(meta_dict['subject'])
        year     = date[0:4]
        
        return map(cleanup_rec, [rec_id, authors, title, abstract, info, subject, year])
    
    rows = (prepare_meta_row(rec_id,meta_dict) for rec_id,meta_dict in get_meta_from_pkl(pkl_dir))

    # Write rows, 10.000 per transaction
    for batch_count, batch in enumerate(group_generator(rows,10000)):
        if batch_count == max_batch: break
        if DEBUG: print "Processing batch ", batch_count
        with con:
            cur.executemany("INSERT INTO meta VALUES(?, ?, ?, ?, ?, ?, ?)", batch)

        

def fill_author_table(db_file,pkl_dir=pkl_dir, max_batch = -1):
    """ 
    Creates a lookup table with schema: author, year, arxiv_id, title
    All elements from each 'creator' value in meta_dict give rows of the ayit table.
    """

    # Initialize db
    con = lite.connect(db_file)

    # Write meta table
    with con:
        cur = con.cursor()
        cur.execute("DROP TABLE IF EXISTS ayit_lookup")
        cur.execute("CREATE TABLE ayit_lookup(author TEXT, year INT, arxiv_id TEXT, title TEXT)")

    def prepare_ayit_row(rec_id,meta_dict):
        title   = meta_dict['title'][0]
        date    = meta_dict['date'][0] 
        year    = date[0:4]
        
        for author in meta_dict['creator']:
            author = author.split(',')[0] 
            yield map(cleanup_rec,[author,year,rec_id, title])
    
    # take union/chain of all generators returned by prepare_ayit_row
    rows = ( row for rec_id,meta_dict in get_meta_from_pkl(pkl_dir) 
                 for row in prepare_ayit_row(rec_id,meta_dict) )


    # Write rows, 10.000 per transaction
    for batch_count, batch in enumerate(group_generator(rows,10000)):
        if batch_count == max_batch: break
        if DEBUG: print "Processing batch ", batch_count
        with con:
            cur.executemany("INSERT INTO ayit_lookup VALUES(?, ?, ?, ?)", batch)
        


def cleanup_rec(string):
    ''' 
    converst to ascii and removes '\n' and '|' from string 
    '''
    if not 'rx' in dir(cleanup_rec):
        cleanup_rec.rx = re.compile(r'[\n|]')

    return cleanup_rec.rx.sub('',to_ascii(string))


    
if __name__ == '__main__':   
    DEBUG = 1

    try:
        main()

    except:
        print "EROOR"

        import sys, traceback, pdb
        type, value, tb = sys.exc_info()
        traceback.print_exc()
        pdb.post_mortem(tb)
