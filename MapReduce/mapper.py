from RefExtract import RefExtract

import os
import multiprocessing as mp
from time import sleep

gz_queue = mp.Queue()
out_queue = mp.Queue()

data_dir = '/media/ram/RWDATA/'
ref_dir  = 'DATA/REF/'

queued = {}



def fill_queue(gz_queue):
    counter  = 0
    for file_name in os.listdir(data_dir):
        if not file_name.endswith('.gz'):continue
        
        f_path = data_dir + file_name
        if f_path in queued: continue

        gz_queue.put(f_path)
        queued[f_path] = 1
        counter += 1

    print "%d files in Queue. Added %d. " % (gz_queue.qsize(), counter)
        
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
        except:
            print "Error processing", gz_file_name
            continue

        try:
            os.remove(gz_path)
        except:
            pass

 
 
def main():
    M = 6 # Number of Workers
 
    
    # Init Workers
    Workers = [ mp.Process(target=worker,args=(gz_queue,)) for i in range(M) ]
    for w in Workers: w.start()
    
    while True:
        fill_queue(gz_queue)
        sleep(3)



if __name__ == '__main__':   
    import os, sys
    import argparse


    import ipdb as pdb
    BREAK = pdb.set_trace
    
    try:
        main()
        pass

    except:
        import sys, traceback
        type, value, tb = sys.exc_info()
        traceback.print_exc()
        pdb.post_mortem(tb)


def old_fill_queue(gz_queue):
    counter  = 0
    for (dir_path,sub_dirs,files) in os.walk(data_dir):
        if dir_path == '.': continue # skip root
        if dir_path.endswith('REF'): continue

        gz_files = filter(lambda x: x.endswith('.gz'), files)
        
        for file_name in gz_files:
            f_path = dir_path + '/' + file_name
            if f_path in queued: continue

            gz_queue.put(f_path)
            queued[f_path] = 1
            counter += 1

    print "%d files in Queue. Added %d. " % (gz_queue.qsize(), counter)
