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
    
    #remove latex comments, to avoid confusion in processing
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

            #trim the string
            bibstring_to_process = bibitem.strip()
            #print "Abibstring_to_process:\t", bibstring_to_process

            (arxiv_id, bibstring_to_process) = extract_arxiv_id(bibstring_to_process)
            #print "Bbibstring_to_process:\t", bibstring_to_process

            (label, key, bibstring_to_process) = extract_label_key(bibstring_to_process)
            #print "Cbibstring_to_process:\t", bibstring_to_process

            (authors, bibstring_to_process) = extract_authors(bibstring_to_process)
            #print "Dbibstring_to_process:\t", bibstring_to_process

            (title, bibstring_to_process) = extract_title(bibstring_to_process)
            print "Ebibstring_to_process:\t", bibstring_to_process
            
            
            print "Counter: %i\tarxiv_id: %s\tlabel: %s\tkey: %s\tauthors: %s\ttitle: %s" % (counter, arxiv_id, label, key, authors, title)
            print "bibstring_to_process:\t", bibstring_to_process
            print bibitem, "\n"
            counter += 1
            #break
            
            
        
    
    #out = open(args.outfile,'w')
    #out.write(json.dumps(d,indent=4))
    #out.close()

def extract_arxiv_id(bibitem):
    #New arxiv citation format
    match = re.search(r'arxiv\:(?P<arxiv>\d{4}\.\d{4}(v\d+)?)', bibitem, re.IGNORECASE)
    if match:
        return (match.group('arxiv'), re.sub(r'arxiv\:\d{4}\.\d{4}(v\d+)?', "", bibitem, 0, re.IGNORECASE).strip())
    else:
        #try old arxiv citation format
        match = re.search(r'arxiv\:(?P<arxiv>[\w\-]+\/\d{7}(v\d+)?)', bibitem, re.IGNORECASE)
        if match:
            return (match.group('arxiv'), re.sub(r'arxiv\:[\w\-]+\/\d{7}(v\d+)?', "", bibitem, 0, re.IGNORECASE).strip())
        else:
            return (None, bibitem)


def extract_label_key(bibitem):
    match = re.match(r'^(\[(?P<label>[^\]]+)\])?\{(?P<key>[^\}]+)\}', bibitem)
    if match:
        return (match.group('label'), match.group('key'), re.sub(r'^(\[[^\]]+\])?\{[^\}]+\}', "", bibitem).strip())
    else:
        return (None, None, bibitem.strip())

def extract_authors(bibitem):
    #try to split citation by \newblock and assume first section is the author list (it usually is?!)
    sections = re.split(r'\\newblock', bibitem, 1)
    if (len(sections) > 1):
        return (sections[0].strip(), sections[1].strip())
    else:
		#instead try to split on \em or \emph, as that usually demarcates the title
        sections = re.split(r'\\emp?h?', bibitem, 1)
        if (len(sections) > 1):
            return (sections[0].strip(), sections[1].strip())
        else:
            return (None, bibitem)


def extract_title(bibitem):
    #try to split citation by \newblock and assume first section is the title (authors already removed)
    sections = re.split(r'\\newblock', bibitem, 1)
    if (len(sections) > 1):
        return (sections[0].strip(), sections[1].strip())
    else:
        sections = re.split(r'\\emp?h?', bibitem, 1)
        if (len(sections) > 1):
            print sections
            return (sections[0].strip(), sections[1].strip())
        else:
            return (None, None) #FIXME


    
    
    #match = re.match(r'^(?P<authors>((?!\\newblock).)*)\s*', bibitem)
    #if match:
    #    return (match.group('authors'), re.sub(r'^((?!\\newblock).)*\\newblock\s*', "", bibitem))
    #else:
    #    #No \newblock, need to split on something else
    #    return (None, bibitem)




# run this directly if required
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("arxivid", help="the arxivId of the source document")
    parser.add_argument("infile", help="location of file to parse")
    parser.add_argument("outfile", help="location of file to output to")
    args = parser.parse_args()
    process(args.arxivid, args.infile, args.outfile)