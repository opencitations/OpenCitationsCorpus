#!/usr/bin/env python
#
# (CC BY-SA 3.0) 2012 Heinrich Hartmann
# 

from nb_input import nbRawInput
import os
from subprocess import call
import file_queue as fq

extraction_queue = '/home/heinrich/Desktop/related-work/BucketControl/extraction_queue.txt'
extract_dir = '/media/ram/RWDATA/'
tmp_dir = '/media/ram/tmp/'

DEBUG = 1

def main():
    print 'Press "x" to break'
    while True:
        file_name = fq.get(extraction_queue)
        if file_name is None: break

        if DEBUG: print "Extracting" , file_name
        a = call(['tar','xf',file_name,'-C',tmp_dir])
        b = call('find %s -name *.gz -type f -exec mv {} %s \;' % (tmp_dir, extract_dir), shell = True)
        c = call('rm -R ' + tmp_dir + '*', shell=True)

        if a == 0 and b == 0 and c == 0:
            fq.pop(extraction_queue)
        else:
            print "ERROR"
            break

        # break if <esc> was pressed
        if nbRawInput('',timeout=1) == 'x':
            break

if __name__ == '__main__':   
    main()
