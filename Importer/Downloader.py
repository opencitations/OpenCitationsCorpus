#based on Heinrich Hartmann's scripts, related-work.net,  2012


import os
from subprocess import call
import sys
sys.path.append('../ImportArxiv/tools')  #TODO: Tidy this up
import file_queue as fq
from nb_input import nbRawInput

class DownloadArXiv(object):
    """Methods to download an extract arXiv files.
    """

    def __init__(self):
        # We change the directory later on. Therefore all paths have to be absolute here.
        self.cur_dir = os.getcwd()
        self.contents_file = self.cur_dir + '/DATA/arXiv/arxiv_s3_downloads.txt'
        self.s3_cmd_ex     = self.cur_dir + "/../ImportArxiv/tools/s3cmd/s3cmd" #TODO: Tidy this up
        self.dl_dir        = self.cur_dir + '/DATA/arXiv/downloads/'


    def download(self):
        if not os.path.exists(self.dl_dir):
            os.makedirs(self.dl_dir)

        os.chdir(self.dl_dir)

        print "Press 'x' to suspend after the current download."
        while True:
            line = fq.get(self.contents_file)
            if line == None: 
                break

            print "Processing ", line
    
            return_code = call([self.s3_cmd_ex,'get','--add-header=x-amz-request-payer: requester','--skip-existing',line])

            if return_code != 0:
                print "ERROR downloading", line 
                break

            fq.pop(self.contents_file)
            # break if x was pressed
            if 'x' in nbRawInput('',timeout=1):
                print "Download suspended. Restart script to resume."
                break
