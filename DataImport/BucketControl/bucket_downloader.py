import os
from subprocess import call

import file_queue as fq

import ipdb
BREAK = ipdb.set_trace

contents_file = 's3_contents.txt'
dl_dir = '/media/1TB-Segate/arxiv_src_buckets/'

s3_cmd_ex = "/home/heinrich/Desktop/related-work/OLD/arxiv_s3_buckets/tools/s3cmd-1.0.0/s3cmd"

cur_dir = os.getcwd() + '/'
os.chdir(dl_dir)

for line in fq.queue(cur_dir + contents_file):
    print "Processing ", line
    
    return_code = call([s3_cmd_ex,'get','--add-header=x-amz-request-payer: requester',line])

    if return_code != 0:
        print "ERROR processing", line 
        break

