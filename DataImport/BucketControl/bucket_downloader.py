import os
from subprocess import call

import sys
sys.path.append('../tools')
import file_queue as fq
from nb_input import nbRawInput

# We change the directory later on. Therefore all paths have to be absolute here.
cur_dir = os.getcwd()

contents_file = cur_dir + '/s3_contents.txt'
s3_cmd_ex     = cur_dir + "/s3cmd-1.0.0/s3cmd"
dl_dir        = cur_dir + '/../DATA/BUCKETS/'

if not os.path.exists(dl_dir):
    os.makedirs(dl_dir)

os.chdir(dl_dir)

print "Press 'x' to suspend after the current download."
while True:
    line = fq.get(contents_file)
    if line == None: 
        break

    print "Processing ", line
    
    return_code = call([s3_cmd_ex,'get','--add-header=x-amz-request-payer: requester',line])

    if return_code != 0:
        print "ERROR downloading", line 
        break

    fq.pop(contents_file)
    # break if x was pressed
    if nbRawInput('',timeout=1) == 'x':
        print "Download suspended. Restart script to resume."
        break
