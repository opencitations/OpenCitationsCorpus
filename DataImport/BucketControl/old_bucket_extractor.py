#!/usr/bin/env python
#
# (CC BY-SA 3.0) 2012 Heinrich Hartmann
# 

import os
from subprocess import call
import file_queue as fq

extraction_queue = '/home/heinrich/Desktop/related-work/arxiv_s3_buckets/buckets/extraction_queue.txt'
extract_dir   =    '/home/heinrich/Desktop/related-work/DATA/'

DEBUG = 1

def main():
    for file_name in fq.queue(extraction_queue):
        if DEBUG: print "Extracting" , file_name
        call(['tar','xf',file_name,'-C',extract_dir])
        for sub_dir in os.listdir(extract_dir):
            if not os.path.isdir(extract_dir + sub_dir):
                continue

            for sub_file in os.listdir(extract_dir + sub_dir):
                if sub_file.endswith('.gz'):
                    os.rename(extract_dir + sub_dir + '/' + sub_file, extract_dir + sub_file)
                if sub_file.endswith('.pdf'):
                    os.remove(extract_dir + sub_dir + '/' + sub_file) # delete pdf's
        
            os.rmdir(extract_dir + sub_dir)

        # Process only one!
        break

if __name__ == '__main__':   
    import ipdb as pdb
    BREAK = pdb.set_trace

    try:
        main()

    except:
        import sys, traceback
        type, value, tb = sys.exc_info()
        traceback.print_exc()
        pdb.post_mortem(tb)
