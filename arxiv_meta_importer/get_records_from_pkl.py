#
#
# Takes pickled oa-metadata entries
# and extracts a record list of the form:
# 
# 1002.1324:Hulek, Klaus and Kaiser, Tilll; Wir grunden einen Kindergarten; doi: , id... ; 2008-02-01
# 

import os, pickle 
base_dir = os.getcwd() + '/'

pkl_dir     = base_dir + 'metadata_pkl/'
meta_list_dir  = base_dir + 'reflists/'

import re
from collections import defaultdict


def main():
    bulk_pkl_to_reflist(pkl_dir,meta_list_dir)

def bulk_pkl_to_reflist(pkl_dir,meta_list_dir):
    
    for pkl_file_name in os.listdir(pkl_dir):
        if not pkl_file_name.endswith('.pkl'): continue
        
        rec_batches = group_gen(oa_extract_refs(pkl_dir + pkl_file_name),10000)

        for batch_count, batch in enumerate(rec_batches):

            if DEBUG: print "Processing ", pkl_file_name, " - ", batch_count
            meta_list_file = meta_list_dir + pkl_file_name[:-4] + '.%03d.txt' % batch_count

            # SKIP WRITES!
            # continue

            try:
                fh = open(meta_list_file,'w')
                fh.write('\n'.join(batch))
                fh.close()
            except:
                print "Error writing batch ", meta_list_file


def oa_extract_refs(pkl_file_path):
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
            rec_id = oa_id.split(':')[-1].ljust(18,'_')
            # gives: 'astro-ph/0001516__'
        else:
            rec_id = oa_id[-9:].ljust(18,'_')
        
        authors = meta_dict['creator']
        title   = meta_dict['title']
        IDs      = meta_dict['identifier']  # journal etc.
        date    = meta_dict['date'][0] 

        rec_text = '; '.join([
                rec_id+':'+        # Arxiv id
                ' and '.join(authors), # Authors 
                title[0],              # title
                ', '.join(IDs),        
                date ])
        
        yield to_ascii(rec_text)


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
    return normalize('NFKD', unicode_string).encode('ascii','ignore')

    
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
