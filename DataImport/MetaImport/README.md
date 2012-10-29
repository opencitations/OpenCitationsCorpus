These scripts manage the metadata import from arxiv.org

## MetaHarvester.py 
   
This is a standalone script that downloads the files from the arxiv
OAI interface.  By default the data is serialized as pikle and
stored in a subdirectory 'metadata_pkl' which has to be
created.

See the comments or 'MetaHarvester.py --help' for usage
instructions.
   
## MetaRead.py 

Python module for using the harvested data in other python scripts.

## MetaExport.py

Export the harvested metadata as *.txt files and sqlitedb.