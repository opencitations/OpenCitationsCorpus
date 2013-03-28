#!/usr/bin/env python
# encoding: utf-8
"""
Runner.py

Created by Martyn Whitwell on 2013-03-14.

"""

import sys
import os
import re

# matches \em{, \emph{, {\em, {\emph, \textit{, {\textit
_re_starts_with_emph_tag = re.compile(r'^\s*(\{\\emp?h?\s+|\\emp?h?\{|\{\\textit\s+|\\textit\{)')

# matches \em, \emph, \textit
_re_split_emph_tag = re.compile(r'(\\emp?h?|\\textit)')
_re_split_newblock = re.compile(r'\\newblock')



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
    sections = _re_split_newblock.split(bibitem, 1)
    if (len(sections) > 1):
        # call remove_wrapping_curly_braces() as sometimes the records are wrapped in them. A full parser is not necessary in this case.
        (authors, remainder) = (remove_wrapping_curly_braces(sections[0]), sections[-1])
    else:
        #instead try to split on \em or \emph or \textit, as that usually demarcates the title
        sections = _re_split_emph_tag.split(bibitem, 1)
        if (len(sections) > 1):
            # call remove_wrapping_curly_braces() as sometimes the records are wrapped in them. A full parser is not necessary in this case.
            (authors, remainder) = (remove_wrapping_curly_braces(sections[0]), "\emph" + sections[-1])
        else:
            # try to split on \<space> as some publications have used this
            sections = re.split(r'\\\s+', bibitem, 1)
            if (len(sections) > 1):
                # call remove_wrapping_curly_braces() as sometimes the records are wrapped in them. A full parser is not necessary in this case.
                (authors, remainder) = (remove_wrapping_curly_braces(sections[0]), sections[-1])
            else:
                # give up and assume that the whole bibitem are the authors
                (authors, remainder) = (bibitem, "")
    authors = remove_end_punctuation(authors.strip())
    if len(authors) == 0:
        authors = None
    return (authors, remainder.strip())


def extract_title(bibitem):
    # Ok, this is not so trivial!
    # First we will see if there is a \newblock, and if so, assume that the title is everything in front of the first \newblock
    # NB. You must call extract_authors() first to parse out the authors first before the title, as they will be infront of an earlier \newblock
    sections = _re_split_newblock.split(bibitem, 1)
    if (len(sections) > 1):
        # sometimes the title can be in an {\em } tag or \em{ } tag or \textit{} tag, inside of the \newblock section. In this case, extract using the full parser
        match = _re_starts_with_emph_tag.match(bibitem)
        if match:
            (title, remainder) = full_parse_curly_braces(bibitem, 1, 1) #assume first bracket at level 1
            #TODO strip out \em in title
        else:
            # call remove_wrapping_curly_braces() as sometimes the records are wrapped in them. A full parser is not necessary in this case.
            (title, remainder) = (remove_wrapping_curly_braces(sections[0]), sections[1])
    else:
        # No \newblock was found. So we need to try and parse on something else
        # Check to see if the bibitem starts with \emph{ or {\emph }. If so, assume the title is contained inside the \emph{} tag
        # In this case, a full parser is required to extract the title, a regex is insufficient.
        match = re.match(r'^\s*(\{\\emp?h?\s+|\\emp?h?\{)', bibitem)
        if match:
            (title, remainder) = full_parse_curly_braces(bibitem, 1, 1) #assume first brack at level 1
        else:
            # No \newblock or \emph{ was found. Instead, try to split on first full stop + space
            sections = re.split(r'\.\s+', bibitem, 1)
            if (len(sections) > 1):
                (title, remainder) = (sections[0], sections[1])
            else:
                # Ok, at this point we are not doing very well. Try to split on a full stop.
                sections = re.split(r'\.', bibitem, 1)
                if (len(sections) > 1):
                    (title, remainder) = (sections[0], sections[1])
                else:
                    # One last try - we've attempted, \newblock, \emph, fullstop+space, fullstop. Now try a comma+space.
                    sections = re.split(r'\,\s+', bibitem, 1)
                    if (len(sections) > 1):
                        (title, remainder) = (sections[0], sections[1])
                    else:
                        # Ok time to give up. Either we can assume that the whole string is a title, or that there is no title.
                        # Lets go with the former.
                        (title, remainder) = (bibitem, "")

    # Finally, lets tidy-up the title and return it
    return (remove_end_punctuation(title.strip()), remainder.strip())



def remove_end_punctuation(bibitem):
    return re.sub(r'[\.\,\s]+$', "", bibitem)



def full_parse_curly_braces(bibitem, brace_level=1, brace_number=1):
    # This method iterates over a string, analysing the curly-braces contained therein. 
    # It extracts the data for the specified level (and above) and specified brace number
    #
    # Some examples:
    #
    # INPUT:
    #   bibitem = "level 0 { level 1a {level 2} level 1a} level 0 {level 1b} level 0"
    #   brace_level = 1
    #   brace_number = 1
    # RESULT:
    #   parsed ==> "level 1a {level 2} level 1a"
    #   remainder ==> "level 0 {} level 0 {level 1b} level 0"
    #
    # INPUT:
    #   bibitem = "level 0 { level 1a {level 2} level 1a} level 0 {level 1b} level 0"
    #   brace_level = 1
    #   brace_number = 2
    # RESULT:
    #   parsed ==> "level 1b"
    #   remainder ==> "level 0 { level 1a {level 2} level 1a} level 0 {} level 0"
    #
    # INPUT:
    #   bibitem = "level 0 { level 1a {level 2} level 1a} level 0 {level 1b} level 0"
    #   brace_level = 2
    #   brace_number = 1
    # RESULT:
    #   parsed ==> "level 2"
    #   remainder ==> "level 0 { level 1a {} level 1a} level 0 {level 1b} level 0"
    
    parser_level = 0
    brace_count = 0
    parsed = ""
    remainder = ""

    # iterate over every character in the string
    for char in bibitem.strip():

        # if we are closing the brace, decrement the parser_level
        if char == '}':         
            parser_level -= 1
        
        # if we are at or above the desired level, and in the correct brace_number, then parse the string
        # otherwise, store the string in the remainder
        if parser_level >= brace_level and brace_count == brace_number:
            parsed += char
        else:
            remainder += char

        # if we are opening the brace, increment the parser_level            
        if char == '{':
            parser_level += 1
            #if we are now on the desired level, then increment the brace_count
            if parser_level == brace_level:
                brace_count += 1

    # if the parsed string starts with '\em ' then this can be removed
    parsed = re.sub(r'^\\emp?h?\s+', "", parsed, 1)
    return (parsed, remainder)
    

    
def remove_wrapping_curly_braces(bibitem):
    match = re.match(r'^\s*\{(?P<value>.+)\}\.?\s*$', bibitem)
    if match:
        return match.group('value').strip()
    else:
        return bibitem






# run this directly if required
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("arxivid", help="the arxivId of the source document")
    parser.add_argument("infile", help="location of file to parse")
    parser.add_argument("outfile", help="location of file to output to")
    args = parser.parse_args()
    process(args.arxivid, args.infile, args.outfile)