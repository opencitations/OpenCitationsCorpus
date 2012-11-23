# Arxiv S3 Bucket download scripts

This scripts will download the arxiv tex-sources from the amazon s3
cloud.  You will be __charged__ for the download by Amazon for the
download.  A full download of all 250GB source files will cost around
30$.

This script relies on the [http://s3tools.org/s3cmd](s3cmd) tool to
access the amazon s3 storage. Which we include here for user
convenience.  It was patched
(cf. [http://arxiv.org/help/bulk_data_s3](arxiv bulk donload)) in
order to work with the arxiv repositoty.

__DISCLAIMER__
The programm s3cmd is released under GNU Public License v2 (GPLv2) by
s3tools.org and we included it here for convenience.  
Apart from the small patch we did not modify s3cmd at all. 
CREDITS GO TO s3tools.org!

You will have to run 's3cmd --configure' and enter yout amazon account
details.

The file list 's3_contentes.txt' will be used as a checklist, addings
'#' on all lines which we have started to dowload.  We filled the file
with a directory listing dating from October 2012.  To update the list
use the output of './s3cmd ls --add-header="x-amz-request-payer:
requester" s3://arxiv/src/''

## bucket_downloader.py 

Will download all (unchecked) files listed in 's3_contents.txt' to the
'BUCKET' folder.  This script resumes where it left of by default.

## bucket_extractor.py

Will extract all files in 'BUCKET' folder to the 'DATA/SOURCES'
folder. This script es managed by a checklist 'extraction_queue.txt'
which enables you to interrupt this script (by pressing 'x') and
continue where you left of. Delete the file if you want to extract
everything again.

This script will create several 100.000's of files inside 'DATA/SOURCES'
which causes considerable stress to the file system. It is therefore
recommended to start the next step, reference extraction via the MapReduce 
scripts, in parallel.