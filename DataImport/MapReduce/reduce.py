#!/usr/bin/env python
#
# Automated reference extraction from gz package
#
#                        (CC BY-SA 3.0) 2012 Heinrich Hartmann
# 


import os
from time import sleep

dir_name = '../DATA/REF/'
out_file = '../DATA/ALL_REF.txt'

while True:
    files = os.listdir(dir_name)
    print "Reducing %d files" % len(files)
    # Concatenate files
    out = ''
    for file_name in files:
        if not file_name.endswith('ref.txt'): continue
        with open(dir_name + file_name) as fh:
            out += fh.read()

    # Write to output
    try:
        wh = open(out_file,'a')
        wh.write(out)
        wh.close()
    except:
        raise IOError('Error writing '+out_file)

    # Remove sources
    for file_name in files:
        if not file_name.endswith('ref.txt'): continue
        os.remove(dir_name + file_name)


    sleep(1)
