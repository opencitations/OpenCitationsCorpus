#
# Automatic Arxiv s3-bucket extraction management
# 
# Papers arrive as gz-files in the gz/ folder 
# 
# * extracts files into src/
# * cleans up: 
#      deletes images, restores file extensions
#      deletes pdf and ps figures 
# * merges tex and bbl files into one container
# * sorts files:
#   - *.tex into tex/ folder
#   - *.bbl into bbl/ folder
#   - *.pdf ...
#   - *.ps  
#
#
#                                                4. extract
#  +------+  1.unzip  +-------+ 3.sort   +------+   bibliography
#  |bucket| --------> |  src  | -------> | tex  |----+
#  +------+           +-------+    |     +------+    |        
#     |              2.cleanup     |                 |
#     |                merge       |     +------+<---+         
#     |                            +---> | bbl  | ------------->   reflist.txt
#     |      +-----+                     +------+  5. extract 
#     +----->| pdf |                                  bibitems 
#            +-----+
#
#


import os
import tarfile, gzip, cStringIO, shutil, os
import tools.pymagic.magic as magic
FileTypeDetector = magic.Magic()

from gz_extraction import *
from cleanup_tex_dir import *
from helper_functions import *
from tex_ref_extractor import *

DEBUG = 1

def main():

    base_dir = os.getcwd() + '/'

    bucket_dir = base_dir + 'buckets/EXTRACTED/'
    src_dir    = base_dir + 'PROGRESS/src/'
    tex_dir    = base_dir + 'PROGRESS/tex/'
    bbl_dir    = base_dir + 'PROGRESS/bbl/'
    pdf_dir    = base_dir + 'PROGRESS/pdf/'
    reflist    = base_dir + 'PROGRESS/reflist.txt'
    
    # Create dirs if not already there
    prepare_dirs([src_dir,tex_dir,pdf_dir,bbl_dir])
    
    # Take pdf files out of the way
    sort_files_by_extension(bucket_dir, guide_book={ '.pdf': pdf_dir })
    
    # 1. Extracting
    bulk_extract_gz(bucket_dir, src_dir, remove_gz = False )
        
    # 2. Cleaning
    clean_up_src(src_dir)
    
    # 3. Merge and Sorting
    merge_by_extension(src_dir,['.tex','.bbl'])
    sort_files_by_extension(src_dir, guide_book={
            '.tex': tex_dir,
            '.bbl': bbl_dir
            })

    # 4. 'thebibliography' from tex files
    bulk_extract_bib_section(tex_dir,bbl_dir, remove_tex = True )

    # 5. Write bbl entries to reflist
    bulk_extract_bibitems(bbl_dir,reflist, remove_bbl = True)

if __name__ == '__main__':   
    DEBUG = 1
    import pdb as pdb
    BREAK = pdb.set_trace

    try:
        main()

    except:
        print "EROOR"

        import sys, pdb, traceback
        type, value, tb = sys.exc_info()
        traceback.print_exc()
        pdb.post_mortem(tb)
