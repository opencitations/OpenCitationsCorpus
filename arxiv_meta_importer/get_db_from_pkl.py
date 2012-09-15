#
#
# Takes pickled oa-metadata entries
# and extracts a record list of the form:
# 
# 1002.1324:Hulek, Klaus and Kaiser, Tilll; Wir grunden einen Kindergarten; doi: , id... ; 2008-02-01
# 

import os, pickle 

base_dir      = os.getcwd() + '/'
pkl_dir       = base_dir + 'metadata_pkl/'
txt_list_dir  = base_dir + 'reflists/'
db_file       = base_dir + 'meta_records.db'

import sqlite3 as lite

from collections import defaultdict


def main():
    bulk_pkl_to_db(pkl_dir,txt_list_dir)

def bulk_pkl_to_db(pkl_dir,txt_list_dir):
    BREAK()

    con = lite.connect(db_file)
    with con:
        cur = con.cursor()
        cur.execute("DROP TABLE IF EXISTS meta")
        cur.execute("CREATE TABLE meta(arxivid TEXT, autor TEXT, titel TEXT, info TEXT, date TEXT, subject TEXT)")
    
    for pkl_file_name in os.listdir(pkl_dir):
        if not pkl_file_name.endswith('.pkl'): continue

        rec_batches = group_gen(oa_extract_db_recs(pkl_dir + pkl_file_name),10000)


        for batch_count, batch in enumerate(rec_batches):
            if DEBUG: print "Processing ", pkl_file_name, " - ", batch_count
            with con:
                cur.executemany("INSERT INTO meta VALUES(?, ?, ?, ?, ?, ?)", batch)




def oa_extract_db_recs(pkl_file_path):
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

        yield map(to_ascii,rec)
        

def group_list(lst, n):
    n = int(n)
    for i in range(len(lst)/n + 1):
        start = i*n
        end   = min( (i+1)*n, len(lst) )
        if not start == end:
            yield lst[start:end]

def group_gen(generator, size):
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
            
    

def to_ascii(unicode_string):
    from unicodedata import normalize
    try:
        return normalize('NFKD', unicode_string).encode('ascii','ignore')
    except TypeError:
        return unicode_string.encode('ascii','ignore')
        
         

    
if __name__ == '__main__':   
    DEBUG = 1

    import pprint 
    pp = pprint.PrettyPrinter(indent=4).pprint

    import ipdb as pdb
    BREAK = pdb.set_trace

    try:
        main()

        BREAK()

    except:
        print "EROOR"

        import sys, traceback
        type, value, tb = sys.exc_info()
        traceback.print_exc()
        pdb.post_mortem(tb)
