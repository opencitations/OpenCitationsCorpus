#!/usr/bin/env python
#
# A very descriptive title of this file should go here
#
# Some further explanation. Bulletpoints are great!
# * ahh here goes the fist one
# * some more text
# * we always need three of them!
#
#
#                                              (CC BY-SA 3.0) 2012 Heinrich Hartmann
# 

from RefExtract import *
import os


def BatchExtractReferences(gz_dir,ref_dir,remove_sources):
    for file_name in os.listdir(gz_dir):
        if not file_name.endswith('gz'): continue
        print "Processing", file_name
        try:
            ref_text = RefExtract(gz_dir + file_name)
            ref_file_name = file_name[:-3] + '.ref.txt'
            wh = open(ref_dir + ref_file_name,'w')
            wh.write(ref_text)
            wh.close()
            os.remove(gz_dir + file_name)
        except:
            print "Error processing", file_name


if __name__ == '__main__':   
    import ipdb as pdb
    BREAK = pdb.set_trace

    global DEBUG

    import argparse    
    parser = argparse.ArgumentParser()
    parser.add_argument('gz_dir', help = 'path to *.gz-files', type=str)
    parser.add_argument('ref_dir', help = 'target dir', type=str)
    parser.add_argument('--remove', help = 'remove source files', action='store_true')
    parser.add_argument('-v','--verbose', help = 'Give detailed status information', action='store_true')
    
    args = parser.parse_args()
    if args.verbose:
        DEBUG = 1

    gz_dir = args.gz_dir
    ref_dir = args.ref_dir
    if not os.path.isdir(gz_dir):
        raise IOError('Not a directory: '+ gz_dir)
    if not os.path.isdir(ref_dir):
        raise IOError('Not a directory: '+ ref_dir)


    if args.remove:
        remove_sources = True
    else:
        remove_sources = False
    
    try:
        BatchExtractReferences(gz_dir,ref_dir,remove_sources)

    except:
        import sys, traceback
        type, value, tb = sys.exc_info()
        traceback.print_exc()
        pdb.post_mortem(tb)
