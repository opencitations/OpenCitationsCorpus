#!/usr/bin/env python
#
# (CC BY-SA 3.0) 2012 Heinrich Hartmann
# 

from subprocess import call
import os, sys

sys.path.append('../tools')
import file_queue as fq

# non-blocking RawInput
from nb_input import nbRawInput

extraction_queue = './extraction_queue.txt'
bucket_dir = '../DATA/BUCKETS/'
extract_dir = '../DATA/SOURCES/'
tmp_dir = './tmp/'

# Resume switch
RESUME = True

def main():
    print 'Press "x" to break'


    if not os.path.exists(tmp_dir):
        os.mkdir(tmp_dir)

    if not os.path.exists(extract_dir):
        os.mkdir(extract_dir)

    if not os.path.exists(extraction_queue) or not RESUME:
        call('find {source_dir} -type f > {target_file}'.format(
                source_dir = bucket_dir,
                target_file = extraction_queue 
                ) , shell = True)

    while True:
        file_name = fq.get(extraction_queue)
        if file_name is None: break

        print "Extracting bucket" , file_name
        if call(['tar','xf',file_name,'-C',tmp_dir]):
            # call returns 1 on error.
            break

        if call('find %s -name *.gz -type f -exec mv {} %s \;' % (tmp_dir, extract_dir), shell = True):
            break

        if call('rm -R ' + tmp_dir + '*', shell=True):
            break

        fq.pop(extraction_queue)

        # break if x was pressed
        if nbRawInput('',timeout=1) == 'x':
            print "Extraction suspended. Restart script to resume."
            break


if __name__ == '__main__':   
    main()
