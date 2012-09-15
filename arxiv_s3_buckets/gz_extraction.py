avoid_extensions = ['eps','epsi','epsc','png','jpg', 'jpeg','gif','fig','eps3',       # Images
                    'sty','cls','clo','bst','log','toc',         # Latex
                    'cry','bak','sh',                            # Other Garbarge
                    'ps','pdf'                                   # virtually only images here
                    ]

from Manager import *

def bulk_extract_gz(source_dir='./',target_dir='./', remove_gz=True):
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
                   prefix = filename[:-3].ljust(18,'_'), # strip off ".gz" add "_"
                   avoid = avoid_extensions
                   )

        if remove_gz:
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

            name = curr_file.name

            # skip extensions in avoid
            if True in [name.endswith(ext) for ext in avoid]: continue

            content = fh.extractfile(curr_file)
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
