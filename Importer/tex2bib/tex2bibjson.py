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

            (url, bibstring_to_process) = extract_url(bibstring_to_process)

            (authors, bibstring_to_process) = extract_authors(bibstring_to_process)
            #print "Dbibstring_to_process:\t", bibstring_to_process


            #print "BeforeTitle:\t", bibstring_to_process
            (title, bibstring_to_process) = extract_title(bibstring_to_process)
            #print "AfterTitle:\t", bibstring_to_process
            
            
            #print "Counter: %i\tarxiv_id: %s\tlabel: %s\tkey: %s\turl: %s\tauthors: %s\ttitle: %s" % (counter, arxiv_id, label, key, url, authors, title)
            print "COUNTER: %i \t AUTHORS: %s \t TITLE: %s" % (counter, authors, title)
            #print "bibstring_to_process:\t", bibstring_to_process
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


def extract_url(bibitem):
    #Extract URL if it is within a \url{} tag
    match = re.search(r'\\url\{(?P<url>https?\:\/\/[^\}]+)\}', bibitem, re.IGNORECASE)
    if match:
        return (match.group('url'), re.sub(r'\\url\{https?\:\/\/[^\}]+\}', "", bibitem, 0, re.IGNORECASE).strip())
    else:
        #Otherwise just try and search for http://
        match = re.search(r'(?P<url>https?\:\/\/[\w\+\&\@\#\/\%\?\=\~\_\-\|\!\:\,\.\;]+[\w\+\&\@\#\/\%\=\~\_\|])', bibitem, re.IGNORECASE)
        if match:
            return (match.group('url'), re.sub(r'https?\:\/\/[\w\+\&\@\#\/\%\?\=\~\_\-\|\!\:\,\.\;]+[\w\+\&\@\#\/\%\=\~\_\|]', "", bibitem, 0, re.IGNORECASE).strip())
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
        return (remove_end_punctuation(remove_curly_braces_wrapper(sections[0].strip())), sections[1].strip())
    else:
        #instead try to split on \em or \emph, as that usually demarcates the title
        sections = re.split(r'\\emp?h?', bibitem, 1)
        if (len(sections) > 1):
            return (remove_end_punctuation(remove_curly_braces_wrapper(sections[0].strip())), "\emph" + sections[1].strip())
        else:
            return (None, bibitem)


def extract_title(bibitem):
	# Ok, this is not so trivial!
	# First we will see if there is a \newblock, and if so, assume that the title is everything in front of the first \newblock
	# You must parse out the authors first before the title, as they will be infront of an earlier \newblock
    sections = re.split(r'\\newblock', bibitem, 1)
    if (len(sections) > 1):
        #sometimes the title can be in an {\em } tag inside of the \newblock section. In this case, extract it
        match = re.match(r'\s*\{\\emp?h?\s+(?P<title>[^\}]+)\}', sections[0])
        if match:
            return (remove_end_punctuation(match.group('title').strip()), re.sub(r'\s*\{\\emp?h?\s+[^\}]+\}', "", sections[0]).strip() + " " + sections[1].strip())
        else:
            return (remove_end_punctuation(remove_curly_braces_wrapper(sections[0].strip())), sections[1].strip())
    else:
		# No \newblock was found. So we need to try and parse on something else
		# Check to see if the bibitem starts with \emph{. If so, assume the title is contained inside the \emph{} tag
		# In this case, a full parser is required to extract the title, a regex is insufficient as it cannot match
		# this case: \emph{this is {bla} the title ${bla}} bla bla \textbf{1234} => "this is {bla} the title ${bla}"  [not possible in regex]
        match = re.match(r'^\s*\\emp?h?\{', bibitem)
        if match:
            return ("PARSED[" + parse_out_curly_braces(bibitem) + "]", "FIX ME TOO")
        else:
            #try to split on first full stop + space
            sections = re.split(r'\.\s+', bibitem, 1)
            if (len(sections) > 1):
                return (remove_end_punctuation(sections[0].strip()), sections[1].strip())
            else:
                return (None, None) #FIXME




def remove_emph(bibitem):
    match = re.match(r'^\{\em(?P<value>.+)\}\.?\s*$', bibitem)
    if match:
        return match.group('value').strip()
    else:
        return bibitem

def remove_end_punctuation(bibitem):
    return re.sub(r'[\.\,\s]+$', "", bibitem)

    
def remove_curly_braces_wrapper(bibitem):
    match = re.match(r'^\{(?P<value>.+)\}\.?\s*$', bibitem)
    if match:
        return match.group('value').strip()
    else:
        return bibitem

def full_parse_out_curly_braces(bibitem):
    parse_level = 0
    started = False
    value = ""
    for char in bibitem.strip():
        if char == '}':
            parse_level -= 1
            
        if parse_level > 0:
            started = True
            value += char
            
        if char == '{':
            parse_level += 1
        
        if started and parse_level == 0:
            break
    if len(value) > 0:
        return value
    else:
        return None
    
    



# run this directly if required
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("arxivid", help="the arxivId of the source document")
    parser.add_argument("infile", help="location of file to parse")
    parser.add_argument("outfile", help="location of file to output to")
    args = parser.parse_args()
    process(args.arxivid, args.infile, args.outfile)