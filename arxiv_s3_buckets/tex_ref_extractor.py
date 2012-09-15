#!/usr/bin/env python
#
# Flow 1)
#  1. Read tex files from tex_dir
#  2. extract thebibliography section
#  3. write to bbl directory
#
# Flow 2)
#  1. Read files from bbl_dir
#  2. Extract all bibitems + cleanup
#  3. Write to reflist file
#
#        1) extract                 2) extract
# +-----+  thebibliography   +-----+   bibitems
# | tex |------------------->| bbl | ------------> reflixt.txt
# +-----+                    +-----+            
#
#
#  Reflist Content Example:
#
#  1001.0675|R. Guida, J. Zinn-Justin, 3D Ising Model: The Scaling Equation of State, Nucl. Phys. B 489 (1997) 626-652.
#  1001.0675|R. Guida, J. Zinn-Justin, Critical exponents of the N -vector model, J. Phys. A 31 (1998) 8103-8121.
#  1001.0675|H. Kleinert, W. Janke, Convergence behavior of ....
#
#
#

from Manager import *
from helper_functions import *
import os

def main():
    DEBUG = 1

    base_dir = os.getcwd() + '/'
    tex_dir = base_dir + 'PROCESS/tex/'
    bbl_dir = base_dir + 'PROCESS/bbl/'
    reflist = base_dir + 'PROCESS/reflist.txt'

    prepare_dirs([tex_dir,bbl_dir])

    #
    # Extract  'thebibliography' from tex files
    #
    bulk_extract_bib_section(tex_dir,bbl_dir)


    #
    # Extract individual citations from files in bbl_dir
    # Write them into the ref_list file
    #
    bulk_extract_bibitems(bbl_dir,reflist)
    

def bulk_extract_bib_section(tex_dir, bbl_dir, remove_tex = False):
    for file_name, tex_string in read_files_from_dir(tex_dir,'.tex', remove = remove_tex ):
        if DEBUG: print "Extracting bibliographies from ", file_name

        tex_string = clear_tex_comments(tex_string)

        bbl_string = extract_tex_env(tex_string,"thebibliography")
        if bbl_string == "": continue
        
        target_name =  file_name[:-3] + "_from_tex.bbl"
        
        fh = open(bbl_dir + target_name,'w')
        fh.write(bbl_string)
        fh.close()


def extract_tex_env(file_string, env_name):
    """ Merges all "thebibliography" sections from string"""
    
    out = ''
    position = 0 
    while True:
        start_sec   = file_string.find('\\begin{' + env_name + '}',position)
        # Break if we have not found anything
        if start_sec == -1: break

        # Find the closing tag
        end_sec     = file_string.find('\\end{' + env_name + '}',  start_sec)

        # Append contents to out
        out += file_string[ start_sec + len(env_name) + 8  :end_sec] 

        # Go on starting from end of last section
        position = end_sec

    if out != '':
        out ='\\begin{' + env_name + '}' + out + '\\end{' + env_name +'}'

    return out


def clear_tex_comments(tex_string):
    out = ''
    for line in tex_string.splitlines():
        end = line.find('%')
        if end == -1: # no comment in line
            out += line + '\n'
        else:
            out += line[:end] + '\n'
    return out



def bulk_extract_bibitems(bbl_dir,reflist,remove_bbl = False):
    buffer = ''
    # for each bbl_file

    for file_name, bbl_string in read_files_from_dir(bbl_dir,'.bbl', remove = remove_bbl):
        if DEBUG: print 'Extracting bibitems from', file_name

        # some cleaning
        bbl_string = clear_tex_comments(bbl_string)
        bbl_string = strip_thebib_tags(bbl_string)
        
        # write bibitems to file reflist in format
        # ID| refitem
        for entry in get_bibtems(bbl_string):
            buffer += file_name[:9] +"|"+ entry+"\n"


    fh = open(reflist,'w')
    fh.write(buffer)
    fh.close()
        

def strip_thebib_tags(bbl_string):
    start = bbl_string.find('thebibliography') + 21
    end   = bbl_string.rfind('thebibliography') - 5
    return bbl_string[start:end]


import re
clean_rx = re.compile('[^\w.,():/-]+')

def get_bibtems(bbl_string):
    tex_codes = [
        '\\it','\\bf','\\textbf','\\em','\\newblock','\\textsc',
        '\\emph',
        '\\bibinfo{author}','\\bibinfo{pages}','\\bibinfo{title}',
        '\\bibinfo{journal}','\\bibinfo{year}',
        ]

    remove_strings = '''
        textbf endcsname providecommand newblock samestyle csname
        emph href textit author pages title textsc bf citenamefont sc
        bibnamefont bibfnamefont bibinfo BibitemOpen penalty0 bibfield
        '''.split()

    out = []

    for item in bbl_string.split('\\bibitem'):
        # remove label
        label_end = item.find('}')
        item = item[label_end+1:]

        # remove tex code
#        for tag in tex_codes:
#            item = item.replace(tag,'')

        # clean up non alphanumeric junk
        item = clean_rx.sub(' ', item).strip()

        for subs in remove_strings:
            item = item.replace(subs,'')

        if item != '':
            out.append(item)

    return out



if __name__ == '__main__':    
    try:
        DEBUG = 1
        import tools.ipdb as ipdb
        BREAK = ipdb.set_trace
        
        main()

    except:
        print "EROOR"

        import sys, traceback
        type, value, tb = sys.exc_info()
        traceback.print_exc()
        ipdb.post_mortem(tb)
