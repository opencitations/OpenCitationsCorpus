#
# Takes pickled oa-metadata entries
#
# 1. Creates text files with entries:
#    id | authors | title | comments | date | subject
#    example: 
#    1010.5365|Melnikov, Ilarion V. and Minasian, Ruben|Heterotic Sigma Models with N=2 Space-Time Supersymmetry
#             |JHEP 1109:065,2011, doi:10.1007/JHEP09(2011)065|2010-10-26|High Energy Physics - Theory
# 
# 2. Creates a sqlite3 db with schema:
#    meta(arxivid TEXT, autor TEXT, titel TEXT, info TEXT, date TEXT, subject TEXT, year INT)
#
#    We append year as an int field to allow the creation of efficient searching
#
 
import os, pickle, re
import sqlite3 as lite
from unicodedata import normalize

def main():
    base_dir      = os.getcwd() + '/'
    pkl_dir       = base_dir + 'metadata_pkl/'
    txt_list_dir  = base_dir + 'reflists/'
    db_file       = base_dir + 'meta_records_2.db'

    # fill_db_from_pkl(pkl_dir,db_file)
    # bulk_pkl_to_txt(pkl_dir,txt_list_dir)


def get_entries_from_pkl_dir(pkl_dir):
    for pkl_file_name in os.listdir(pkl_dir):
        if not pkl_file_name.endswith('.pkl'): continue

        try:
            fh = open(pkl_dir + pkl_file_name)
            meta_list = pickle.load(fh)
            fh.close()
        except:
            print "Error loading pkl file", pkl_dir + pkl_file_name
            return


        for oa_head,oa_meta,xxx in meta_list:
            try:
                oa_id = oa_head.identifier()
                meta_dict = oa_meta.getMap()
            except:
                print "Error in record found in ", pkl_file_name
                continue

            if '/' in oa_id: # we have an old arxiv identifyer
                # Example: 'oai:arXiv.org:astro-ph/0001516'
                rec_id = oa_id.split(':')[-1]
                # gives: 'astro-ph/0001516'
            else:
                # Example: 'oai:arXiv.org:1001.0231'
                rec_id = oa_id[-9:]

            yield rec_id, meta_dict

    

def fill_db_from_pkl(pkl_dir,db_file, max_batches = -1 ):
    """ 
    Creates a table meta in db_file and inserts records from pkl_files in pkl_dir 
    """

    # Initialize db
    con = lite.connect(db_file)

    # Write meta table
    with con:
        cur = con.cursor()
        cur.execute("DROP TABLE IF EXISTS meta")
        cur.execute("CREATE TABLE meta(arxiv_id TEXT, author TEXT, title TEXT, info TEXT, date TEXT, subject TEXT, year INT)")

        cur.execute("DROP TABLE IF EXISTS ayit_lookup")
        cur.execute("CREATE TABLE ayit_lookup(author TEXT, year INT, arxiv_id TEXT, title TEXT)")

    # Read entries from pkl_dir 10.000 at a time
    for batch_count, batch in enumerate(group_generator(get_entries_from_pkl_dir(pkl_dir),10000)):
        if batch_count == max_batches: break
        if DEBUG: print "Processing batch ", batch_count
        meta_rows = []
        ayit_rows = []

        # convert entries to table schema
        for rec_id, meta_dict in batch:
             authors = ' and '.join(meta_dict['creator'])
             title   = meta_dict['title'][0]
             info    = ', '.join(meta_dict['identifier'][1:])
             date    = meta_dict['date'][0] 
             subject = ', '.join(meta_dict['subject'])
             year    = date[0:4]

             meta_rows.append(map(cleanup_rec,[rec_id, authors, title, info, date, subject, year]))
             
             for author in meta_dict['creator']:
                 author = author.split(',')[0] # only take sir name in here
                 ayit_rows.append(map(cleanup_rec,[author,year,rec_id, title]))

        with con:
            cur.executemany("INSERT INTO meta VALUES(?, ?, ?, ?, ?, ?, ?)", meta_rows)

        with con:
            cur.executemany("INSERT INTO ayit_lookup VALUES(?, ?, ?, ?)", ayit_rows)
        



clean_rx = re.compile(r'[\n|]')
def cleanup_rec(string):
    ''' 
    converst to ascii and removes '\n' and '|' from string 
    '''
    return clean_rx.sub('',to_ascii(string))

    
def to_ascii(unicode_string):
    '''
    Convertes a unicode string to ascii the brutal way
    '''
    try:
        return normalize('NFKD', unicode_string).encode('ascii','ignore')
    except TypeError:
        return unicode_string.encode('ascii','ignore')


def group_generator(generator, size):
    count = 0
    end_flag = False
    while True:
        if end_flag: break
        batch = []
        while True:
            count += 1
            if count % (size + 1) == 0: break

            try:
                item = generator.next()
            except StopIteration:
                end_flag = True
                break

            batch.append(item)

        if not batch == []:
            yield batch








#### TEXT FILE GENERATION #####
# TODO: Use get_entries_from_pkl_dir here, too

def bulk_pkl_to_txt(pkl_dir,txt_dir, batch_size = 10000 ):
    """ 
        Reads records from files in pkl_dir and writes them to text files in txt_dir.
        These text files come in buches of 10.000 entries by default
    """

    rec_count   = 0
    batch_count = 0
    
    fh = open(txt_dir + 'meta_batch_%03d.txt' % batch_count, 'w' )

    buffer = ''
    
    for pkl_file_name in os.listdir(pkl_dir):
        if not pkl_file_name.endswith('.pkl'): continue

        file_recs = oa_extract_recs(pkl_dir + pkl_file_name)

        for rec in file_recs:
            rec_count += 1
            
            buffer += '|'.join(rec) + '\n'
                
            if rec_count % batch_size == 0:
                if DEBUG: print 'Writing meta_batch_%03d.txt' % batch_count, ' - total recs ', rec_count
                fh.write(buffer)
                fh.close()

                batch_count += 1
                fh = open(txt_dir + 'meta_batch_%03d.txt' % batch_count ,'w')

                buffer = ''

    fh.write(buffer)
    fh.close()
    return rec_count



def oa_extract_recs(pkl_file_path):
    """
    reads records from pkl_file, and gives them back in the format
    [rec_id, authors, title,  info, date, subject]
    each entry is converted to ascii and '\n |' characters are removed
    """

    try:
        fh = open(pkl_file_path)
        meta_list = pickle.load(fh)
        fh.close()

    except:
        print "Error loading pkl file", pkl_file_path
        return


    for oa_head,oa_meta,xxx in meta_list:
        try:
            oa_id = oa_head.identifier()
            meta_dict = oa_meta.getMap()
        except:
            print "Error in record found in ", pkl_file_path
            continue


        if '/' in oa_id: # we have an old arxiv identifyer
            # Example: 'oai:arXiv.org:astro-ph/0001516'
            rec_id = oa_id.split(':')[-1]
            # gives: 'astro-ph/0001516'
        else:
            # Example: 'oai:arXiv.org:1001.0231'
            rec_id = oa_id[-9:]
        
        authors = ' and '.join(meta_dict['creator'])
        title   = meta_dict['title'][0]
        info     = ', '.join(meta_dict['identifier'][1:])
        date    = meta_dict['date'][0] 
        subject = ', '.join(meta_dict['subject'])

        rec = [rec_id, authors, title,  info, date, subject]        
        
        yield map(cleanup_rec,rec)

        

def group_list(lst, n):
    n = int(n)
    for i in range(len(lst)/n + 1):
        start = i*n
        end   = min( (i+1)*n, len(lst) )
        if not start == end:
            yield lst[start:end]
            
    
    
if __name__ == '__main__':   
    DEBUG = 1

    import pprint 
    pp = pprint.PrettyPrinter(indent=4).pprint

    import ipdb as pdb
    BREAK = pdb.set_trace

    try:
        main()

    except:
        print "EROOR"

        import sys, traceback
        type, value, tb = sys.exc_info()
        traceback.print_exc()
        pdb.post_mortem(tb)
