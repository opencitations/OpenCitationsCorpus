import gzip, cStringIO, tarfile

import sys
sys.path.append('../tools')
import pymagic.magic as magic
FileTypeDetector = magic.Magic()

def gz_extract(gz_path):
    '''Returns all *.tex and *.bbl files in gz archive concatenated as a single string.
    The contents of the gz file can either be:
    - a tar archive which has not necessarily a proper extension
    - a pdf or tex file, not necessarily having a proper extension
    We use the magic library (included in the tools subdir) to reconstruct the extensions.
    '''
    
    tex_string = ''

    # Unzip the file into memory:
    try:
        gz_fh = gzip.open(gz_path,'rb')
        gz_contents = gz_fh.read()
        gz_fh.close()
    except:
        raise IOError("ERROR: Could not read gz_file " + gz_path)
 
    # Remark: We cannot directly pass gz_fh to tarfile.open
    # this raises a 'ValueError: Seek from end not supported'.
    # Therefor we take the detour with StringIO 

    # Detect filetype with magic library
    filetype = FileTypeDetector.from_buffer(gz_contents[0:1024])
    
    
    if filetype == 'POSIX tar archive (GNU)':
        #  Wrap file_string into a file handler
        try:
            new_gz_fh = cStringIO.StringIO(gz_contents)
            tar_fh = tarfile.open(fileobj = new_gz_fh)
        except:
            raise IOError("ERROR: Could not read open tar file in " + gz_path)


        for sub_file in tar_fh:
            if sub_file.isdir(): continue

            # get file name: flat out subdirs, convert to lower case
            name = sub_file.name.replace('/','_').lower()

            # Do we have a Latex files?
            if not name[-3:] in ['tex','bbl']: continue

            tex_string += '\n\n%%%%%% RELATED-WORK: {0} - {1} %%%%%%\n\n'.format(gz_path,name)
            tex_string += tar_fh.extractfile(sub_file).read().strip()

    else:
        # No tar file? -> Process directly
        
        name = gz_path.split('/')[-1][:-3] 

        if filetype in ['LaTeX 2e document text', 'ASCII English text']:
            tex_string += '\n\n%%%%%% RELATED-WORK: {0} - {1} %%%%%%\n\n'.format(gz_path,name)
            tex_string += gz_contents.strip()

    return tex_string
