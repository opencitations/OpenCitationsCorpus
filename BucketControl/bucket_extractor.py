#!/usr/bin/env python
#
# (CC BY-SA 3.0) 2012 Heinrich Hartmann
# 

from nb_input import nbRawInput
import os
from subprocess import call
import file_queue as fq

extraction_queue = '/home/heinrich/Desktop/related-work/BucketControl/extraction_queue.txt'
extract_dir   =    '/home/heinrich/Desktop/related-work/DATA/'

DEBUG = 1

def main():
    print 'Press "x" to break'
    while True:
        file_name = fq.get(extraction_queue)
        if file_name is None: break

        if DEBUG: print "Extracting" , file_name
        call(['tar','xf',file_name,'-C',extract_dir])

        fq.pop(extraction_queue)

        # break if <esc> was pressed
        if nbRawInput('',timeout=1) == 'x':
            break
        

if __name__ == '__main__':   
    main()


