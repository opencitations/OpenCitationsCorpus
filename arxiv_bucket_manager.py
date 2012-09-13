#
# Automatic bucket extraction
# 


DEBUG = 1
import ipdb
breakpoint = ipdb.set_trace


bucket_dir = '/home/heinrich/Desktop/related_work/arxiv_s3_buckets/1001/'
gz_dir = bucket_dir + 'gz/'
tmp_dir = bucket_dir + 'tmp/'
src_dir = bucket_dir + 'src/'

import tarfile, gzip, cStringIO, magic
import os


FileTypeDetector = magic.Magic()

def extract_to_dir(filename , path='./' , prefix=''): 
    """ Extracts the contents of a given gzipped file 
    to a given path path adding a prefix to all extracted files.
    Example:
    extract_to_dir('a.tar.gz','contents/','a_')

    Creates files a_xxx in the subdirectory 'contents/' for 
    each file xxx in a.tar.gz
    """
    # The contents of the gz file can either be:
    # - a tar archive which has not necessarily a proper extension
    # - a source file
    # We have to distinguish both cases

    # Unzip the file into memory:
    fh = gzip.open(filename,'rb')
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

            if DEBUG: print 'from', filename, 'extracting', name, 'to', path + prefix + name

            target = open(path + prefix + name, 'w')
            target.write( content.read() )
            target.close()

        fh.close()
        unzipped.close()

    else:
        if DEBUG: print "Not a tar archiv! ", filetype

        name = filename.split('/')[-1][:-3]

        if filetype.startswith('LaTeX'):
            name += '.tex'

        target = open(path + prefix + name, 'w')
        target.write( file_string )
        target.close()
    

def bulk_gz_extract(source_path='./',target_path='./'):
    ''' Extracts all gz files in source_path to target_path
    adding a filename prefix.
    
    Example:
    bulk_gz_extract('./','unzip/')
    
    Extract all files x.gz in ./ to unzip/x_(...)'''

    for filename in os.listdir(source_path):
        if not filename.endswith('.gz'): continue

        if DEBUG: print 'Extracting', filename
        extract_to_dir(source_path + filename, target_path, prefix = filename[:-3] + '_')


def clean_up_src(src_path):
    ''' 
    1) Delete Images, Styles
    2) Move *.tex files to ../tex
    3) Move *.bbl files to ../bbl
    ''' 

    RemoveExtensions = ['eps','png','jpg','gif','fig','eps3',       # Images
                        'sty','cls','clo','bst','log','toc',        # Latex
                        'cry','bak','sh'                            # Other Garbarge
                        ]

    # Delete unnecessary files
    for filename in os.listdir(src_path):
        if True in [ filename.endswith(ex) for ex in RemoveExtensions ]:
            if DEBUG: print 'removing', filename
            os.remove(src_path + filename)


    # Sort left over filenames by Arxiv Id's in dictionary. E.g.
    # 
    # file_by_ID['1001.1203'] = ['dawdaw.txt','awdaw.pdf','dwadw.tex']
    #
    file_by_ID = {}

    for filename in os.listdir(src_path):
        ID = filename[:9]
        if not ID in file_by_ID:
            file_by_ID[ID] = [filename]
        else:
            file_by_ID[ID].append(filename)


    for ID, file_list in file_by_ID.items():
        #
        # Tex Files
        #
        # Concat all tex files belonging to a given ID 
        # Write them to ../tex/ID.tex
        #

        tex_file_list = filter(lambda n: n.endswith('tex'), file_list )
        if not tex_file_list == []: 

            source_list = [ src_path + fname for fname in tex_file_list ]
            target_file = src_path + '../tex/'+ID+'.tex'
    
            merge_files(source_list,target_file,remove_sources = True )


        #
        # same with BBL Files
        # 
        bbl_file_list = filter(lambda n: n.endswith('bbl'), file_list )
        if not bbl_file_list == []: 
            source_list = [ src_path + fname for fname in bbl_file_list ]
            target_file = src_path + '../bbl/'+ID+'.bbl'
        
            merge_files(source_list,target_file,remove_sources = True )

        #
        # PS Files
        # 
        # Discard if more than one
        #

        ps_file_list = filter(lambda n: n.endswith('ps'), file_list )
        if not ps_file_list == []:

            if len(ps_file_list) >= 2:
                for file_name in ps_file_list:
                    os.remove(src_path + file_name)

        #
        # PDF Files
        # 
        # Discard if more than one
        #
        pdf_file_list = filter(lambda n: n.endswith('pdf'), file_list )
        if not pdf_file_list == []: 

            if len(pdf_file_list) >= 2:
                for file_name in pdf_file_list:
                    os.remove(src_path + file_name)



def magic_ext_restore(path):
    '''Uses magic lib to restore file extensions '''
    
    extensions={
        'LaTeX 2e document text': '.tex',
        'LaTeX document text'   : '.tex',
        'PostScript document text conforming DSC level 3.0, type EPS' : '.eps'
        }
    
    for file_name in os.listdir(path):
        file_type = FileTypeDetector.from_file(path+file_name)

        if file_type in extensions:
            ext = extensions[file_type]

            os.rename(path + file_name, path + file_name + ext )



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
    


if __name__ == '__main__':    
    try:
        DEBUG = 0
#        bulk_gz_extract(gz_dir,src_dir)
        DEBUG = 1
        clean_up_src(src_dir)
        magic_ext_restore(src_dir)
        clean_up_src(src_dir)

    except:
        print "EROOR"

        import sys, ipdb, traceback
        type, value, tb = sys.exc_info()
        traceback.print_exc()
        ipdb.post_mortem(tb)
