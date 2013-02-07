#
# Automated reference extraction using a hands on map-reduce workflow.
#

import os, sys
import argparse
import multiprocessing as mp
from time import sleep

sys.path.append('../')
from RefExtract import RefExtract


gz_queue = mp.Queue()
out_queue = mp.Queue()

data_dir = '../DATA/SOURCES/'
ref_dir  = '../DATA/REF/'

queued = {}
 
def main():
    if not os.path.exists(ref_dir):
        os.mkdir(ref_dir)

    # Number of Workers
    M = 1
    
    # Init Workers
    Workers = [ mp.Process(target=worker,args=(gz_queue,)) for i in range(M) ]
    for w in Workers: w.start()
    
    while True:
        fill_queue(gz_queue)
        sleep(3)



def fill_queue(gz_queue):
    counter  = 0
    for file_name in os.listdir(data_dir):
        if not file_name.endswith('.gz'):continue
        
        f_path = data_dir + file_name
        if f_path in queued: continue

        gz_queue.put(f_path)
        queued[f_path] = 1
        counter += 1

    print "%d files in Queue. Added %d. " % (counter, counter) # % (gz_queue.qsize(), counter)
        
def worker(gz_queue):
    while True:
        gz_path = gz_queue.get()
        try:
            ref_text = RefExtract(gz_path)
            gz_file_name = os.path.split(gz_path)[-1]
            ref_file_name = gz_file_name[:-3] + '.ref.txt'
            wh = open(ref_dir + ref_file_name,'w')
            wh.write(ref_text)
            wh.close()
        except IOError as e:
            print "Error processing", gz_path, e
            continue

        try:
            os.remove(gz_path)
        except:
            pass



if __name__ == '__main__':   
    try:
        main()

    except:
        import sys, traceback, pdb
        type, value, tb = sys.exc_info()
        traceback.print_exc()
        pdb.post_mortem(tb)

