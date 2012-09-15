from Manager import *
from helper_functions import *

DEBUG = 1

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

    good_extensions  = ['.bbl','.tex'] 

    known_extensions = remove_extensions + good_extensions
        
    for file_name in os.listdir(src_path):
        # Use magic-lib to restore some file extensions of the REMAINING FILES

        # if extension not known
        if not True in [ file_name.endswith(ex) for ex in known_extensions ]:
            # restore extension if possible
            ext = magic_get_extension(src_path+file_name)
            if DEBUG: print 'restoring', file_name, 'with', ext
            os.rename(src_path + file_name, src_path + file_name + ext)

    for file_name in os.listdir(src_path):
        # Delete unnecessary files
        if not True in [ file_name.endswith(ex) for ex in good_extensions ]:
            if DEBUG: print 'removing', file_name
            os.remove(src_path + file_name)



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

