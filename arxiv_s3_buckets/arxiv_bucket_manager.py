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
#                                                   extract
#  +------+   unzip   +-------+   sort   +------+   bibitems     +-------------+ 
#  |bucket| --------> |  src  | -------> | tex  |  ------------> | Ref Strings | 
#  +------+           +-------+    |     +------+   copy         |             | <-+
#     |                cleanup     +---> | bbl  |  ------------> |             |   |
#     |                merge      ?|     +------+   pdfextract   +-------------+   | simple
#     +----------------------------+---->| pdf  | -------------> | Ref - XML   | --+ convert
#       filetype:pdf                     +------+                +-------------+
# 
#
#
#

base_dir = '/home/heinrich/Desktop/related-work/arxiv_s3_buckets/'

bucket_dir  = base_dir + '1201/'

src_dir = base_dir + 'PROCESS/src/'
tex_dir = base_dir + 'PROCESS/tex/'
bbl_dir = base_dir + 'PROCESS/bbl/'
pdf_dir = base_dir + 'PROCESS/pdf/'


import tarfile, gzip, cStringIO, magic
import os, shutil

FileTypeDetector = magic.Magic()
DEBUG = 0


def bulk_extract_gz(source_dir='./',target_dir='./'):
    ''' Extracts all gz files in source_dir to target_dir
    adding a prefix to to extracted file prefix.
    
    Example:
    bulk_gz_extract('./','unzip/')
    
    Extract all files x.gz in ./ to unzip/x_(...)'''

    for filename in os.listdir(source_dir):
        if not filename.endswith('.gz'): continue

        if DEBUG: print 'Extracting', filename
        extract_gz(source_dir + filename, 
                   target_dir, 
                   prefix = filename[:-3] + '_' # strip off ".gz" add "_"
                   )
        os.remove(source_dir + filename)
            


def extract_gz(file_path, target_dir='./' , prefix='', avoid = []): 
    '''Extracts a single gz file into the given path. 
       The contents of the gz file can either be:
       - a tar archive which has not necessarily a proper extension
       - a source file'''

    # Unzip the file into memory:
    fh = gzip.open(file_path,'rb')
    file_string = fh.read()
    fh.close()

    filetype = FileTypeDetector.from_buffer(file_string[0:1024])
    
    if filetype == 'POSIX tar archive (GNU)':
        #  Wrap file_string into a file handler
        unzipped = cStringIO.StringIO(file_string)

        fh = tarfile.open(fileobj = unzipped)

        while True:
            curr_file = fh.next()
            if curr_file is None : break            # Are we finished, yet?
            if curr_file.isdir(): continue          # Skip directories

            content = fh.extractfile(curr_file)
            name = curr_file.name
            name = name.replace('/','_').lower()    # strip subdirs, convert to lower case
            
            target = open(target_dir + prefix + name, 'wb')
            target.write( content.read() )
            target.close()

        fh.close()
        unzipped.close()

    else:
        if DEBUG: print "Not a tar archiv! ", filetype
        # Write file directly to target_dir

        name = file_path.split('/')[-1][:-3] # get filename from path
        target = open(target_dir + prefix + '_no_tar_' + name, 'w')
        target.write(file_string)
        target.close()


def magic_get_extension(file_path):
    restore_dict = {
        'LaTeX 2e document text'  : '.tex',
        'LaTeX document text'     : '.tex',
        'PostScript document text conforming DSC level 3.0, type EPS' : '.eps'
        }

    file_type = FileTypeDetector.from_file(file_path)
    if file_type in restore_dict: 
        return restore_dict[file_type]
    else:
        return ""


def clean_up_src(src_path):
    ''' 
    1) Delete Images, Styles
    2) Restore File Extensions
    ''' 

    remove_extensions = ['eps','epsi','epsc','png','jpg', 'jpeg','gif','fig','eps3',       # Images
                        'sty','cls','clo','bst','log','toc',         # Latex
                        'cry','bak','sh',                            # Other Garbarge
                        'ps','pdf' # virtually only images here
                        ]

    known_extensions  = ['pdf','ps','bbl','tex']


    for file_name in os.listdir(src_path):
        # Delete unnecessary files
        if True in [ file_name.endswith(ex) for ex in remove_extensions ]:
            if DEBUG: print 'removing', file_name
            os.remove(src_path + file_name)
        
    for file_name in os.listdir(src_path):
        # Use magic-lib to restore some file extensions of the REMAINING FILES
        if not True in [ file_name.endswith(ex) for ex in known_extensions ]:
            ext = magic_get_extension(src_path+file_name)
            if DEBUG: print 'restoring', file_name, 'with', ext
            os.rename(src_path + file_name, src_path + file_name + ext)


def sort_files_by_extension(src_dir, guide_book):
    ''' Moves files from src_dir to directories specified in guide.
        Syntax: guide = { '.tex': '/path/to/tex/file/store/', 
                          '.xxx': '/path/to/xxx/file/store/'  }
    '''

    for filename in os.listdir(src_dir):
        for ext, target_dir in guide_book.items():
            if filename.endswith(ext):
                if DEBUG: print "Sorting ", filename, "to", target_dir
                shutil.move(src_dir + filename, target_dir)


def merge_by_extension(src_dir,ext_list):
    ''' Merge all files in a given directory that have
    the same identifyer and an extension in ext_list 
    Example:

    1001.1003_file_1.tex   \ 
    1001.1003_file_2.tex    +==> 1001.1003.tex
    1001.1003_file_3.tex   / 
    1001.1004_file_1.tex    ==> 1001.1004.tex
    '''
    
    file_list = os.listdir(src_dir)

    # Hash files by ID:
    # file_by_ID['1001.1203'] = ['dawdaw.txt','awdaw.pdf','dwadw.tex']
    file_with_id = {}

    for filename in file_list:
        ID = filename[:9]
        if not ID in file_with_id:
            file_with_id[ID] = [filename]
        else:
            file_with_id[ID].append(filename)


    for ID,files in file_with_id.items():
        id_file_list = filter(lambda n: n.startswith(ID), file_list )

        for ext in ext_list:
            ext_file_list = filter(lambda n: n.endswith(ext), id_file_list )
            if ext_file_list == []: continue

            source_list = [ src_dir + name for name in ext_file_list ]
            target_file = src_dir + ID + ext

            merge_files(source_list, target_file, remove_sources = True )




def merge_files(source_list, target_file, 
                seperator="\n%%%%% RELATED-WORK-NET: END OF FILE %%%%\n", 
                remove_sources = False):

    if DEBUG: print 'Merging', source_list , 'to' , target_file
    
    target_fh = open(target_file,'wa')

    for source_file in source_list:
        source_fh = open(source_file, 'r')
        target_fh.write(source_fh.read())
        target_fh.write(seperator)
        source_fh.close()

    target_fh.close()

    if remove_sources:
        for source_file in source_list:
            os.remove(source_file)
    
def prepare_dirs(dir_list):
    for directory in dir_list:
        if not os.path.exists(directory):
            if DEBUG: print 'creating directory', directory
            os.makedirs(directory)


if __name__ == '__main__':    

    DEBUG = 1
    import ipdb
    breakpoint = ipdb.set_trace

    try:
        # Create dirs if not already there
        prepare_dirs([src_dir,tex_dir,pdf_dir,bbl_dir,tex_dir])

        # Take pdf files out of the way
        sort_files_by_extension(bucket_dir, guide_book={ 'pdf': pdf_dir })

        # 1. Extracting
        bulk_extract_gz(bucket_dir, src_dir)
        
        # 2. Cleaning
        clean_up_src(src_dir)
        merge_by_extension(src_dir,['.tex','.bbl'])

        # 3. Sorting
        sort_files_by_extension(src_dir, guide_book={
                'tex': tex_dir,
                'bbl': bbl_dir
                })


    except:
        print "EROOR"

        import sys, ipdb, traceback
        type, value, tb = sys.exc_info()
        traceback.print_exc()
        ipdb.post_mortem(tb)
