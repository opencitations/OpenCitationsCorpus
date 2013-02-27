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
        self.contents_file = self.cur_dir + '/DATA/arXiv/arXiv_s3_downloads.txt'
        self.extraction_queue = self.cur_dir + '/DATA/arXiv/arXiv_extraction_queue.txt'
        self.s3_cmd_ex     = self.cur_dir + "/../ImportArxiv/tools/s3cmd/s3cmd" #TODO: Tidy this up
        self.dl_dir        = self.cur_dir + '/DATA/arXiv/downloads/'
        self.extract_dir =  self.cur_dir + '/DATA/arXiv/sources/'
        self.tmp_dir = self.cur_dir + '/DATA/arXiv/tmp/'

        #self.bucket_dir = '../DATA/BUCKETS/'


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


    def extract(self):
        print 'Press "x" to break'
        if not os.path.exists(self.tmp_dir):
            os.mkdir(self.tmp_dir)

        if not os.path.exists(self.extract_dir):
            os.mkdir(self.extract_dir)

        #Creates arXiv_extraction_queue.txt if it doesn't exist by finding all the tar files in the download folder
        if not os.path.exists(self.extraction_queue):
            call('find {source_dir}*.tar -type f > {target_file}'.format(
                    source_dir = self.dl_dir,
                    target_file = self.extraction_queue 
                    ) , shell = True)

        while True:
            file_name = fq.get(self.extraction_queue)
            if file_name is None: break

            print "Extracting bucket" , file_name
            if call(['tar','xf',file_name,'-C',self.tmp_dir]):
                # call returns 1 on error.
                break

            if call('find %s -name *.gz -type f -exec mv {} %s \;' % (self.tmp_dir, self.extract_dir), shell = True):
                break

            if call('rm -R ' + self.tmp_dir + '*', shell=True):
                break

            fq.pop(self.extraction_queue)

            # break if x was pressed
            if nbRawInput('',timeout=1) == 'x':
                print "Extraction suspended. Restart script to resume."
                break

