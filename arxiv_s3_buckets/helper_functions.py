import os
# import tarfile, gzip, cStringIO, shutil, os

import tools.pymagic.magic as magic
FileTypeDetector = magic.Magic()

DEBUG = 1

def prepare_dirs(dir_list):
    for directory in dir_list:
        if not os.path.exists(directory):
            if DEBUG: print 'creating directory', directory
            os.makedirs(directory)


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

    

def sort_files_by_extension(src_dir, guide_book):
    ''' Moves files from src_dir to directories specified in guide.
        Syntax: guide = { '.tex': '/path/to/tex/file/store/', 
                          '.xxx': '/path/to/xxx/file/store/'  }
    '''

    for filename in os.listdir(src_dir):
        for ext, target_dir in guide_book.items():
            if filename.endswith(ext):
                if DEBUG: print "Sorting ", filename, "to", target_dir
                os.rename(src_dir + filename, target_dir + filename)
                

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



def read_files_from_dir(dir_name,extension='',remove=False):

    for file_name in os.listdir(dir_name):
        if not file_name.endswith(extension): continue
        
        try:
            fh = open(dir_name + file_name,'r')
            text = fh.read()
            fh.close()

            if remove:
                os.remove(dir_name + file_name)
        except:
            print "Error loading file", dir_name + file_name

        yield file_name, text
