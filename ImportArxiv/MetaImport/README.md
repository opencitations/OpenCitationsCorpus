These scripts manage the metadata import from arxiv.org

## Dependicies:

* pyoai/lxml

Use

  sudo apt-get install python-setuptools python-lxml 
  sudo easy_install lxml pyoai

for installation.

## MetaHarvester.py 
This is a standalone script that downloads the
files from the arxiv OAI interface.  By default the data is serialized
as pikle and stored in a subdirectory 'metadata_pkl' which has to be
created.

See the comments or 'MetaHarvester.py --help' for usage
instructions.
   

## MetaExport.py 
Export the harvested metadata as *.txt files and sqlitedb.

## MetaRead.py 
Python module for using the harvested data in other python scripts.

