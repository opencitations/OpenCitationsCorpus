#!/usr/bin/env python
# encoding: utf-8
"""
Runner.py

Created by Martyn Whitwell on 2013-03-14.

"""

import sys
import os
#import OpenCitationsImportLibrary
import re




def process(arxivid, infile, outfile):
    file_handle = open(infile, 'r')
    raw_data = file_handle.read()
    file_handle.close()
    
    #remove commented-out lines
    data = re.sub(r"^\s*\%.*$", "", raw_data, 0, re.MULTILINE)

    #remove whitespace and newlines
    data = re.sub(r"\s+", " ", data, 0, re.MULTILINE)

    #find the bibliography section
    match = re.search(r'\\begin{thebibliography(?P<bibliography>.*)\\end{thebibliography', data, re.DOTALL)
    if match:
        data = match.group('bibliography')

        #get a list of bibitems. Start at [1:] to ignore the stuff between \begin{thebibliography} and \bibitem
        counter=1
        for bibitem in re.split(r"\\bibitem", data)[1:]:
            print counter, bibitem, "\n"
            counter += 1
            
            
        
    
    #out = open(args.outfile,'w')
    #out.write(json.dumps(d,indent=4))
    #out.close()


# run this directly if required
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("arxivid", help="the arxivId of the source document")
    parser.add_argument("infile", help="location of file to parse")
    parser.add_argument("outfile", help="location of file to output to")
    args = parser.parse_args()
    process(args.arxivid, args.infile, args.outfile)