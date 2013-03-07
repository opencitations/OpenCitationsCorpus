# Takes a folder full of NLM MEDLINE xml.gz or NLM PMC OA tar.gz files and converts them to bibJSON
# Every <batchsize> records get batched up and send to an ES index
# Includes provision of all the data required for a BibServer to run on that index

# This script MUST be able to write to disk in the area it runs

# to use:
# make sure you have the modules it will import available
# create a filedir full of the files you got from the ftp site - default expects this to be at ./pmcoa
# check the config.py PMC2ES to see how to change this to run on NLM or other things you can augment. Then:
# import pmc2es
# parser = pmc2es.PMC2ES()
# parser.do()

import requests, json, os, sys
import threading, Queue
from process import Process
import config

filejobs = Queue.Queue()

# a wee class to thread the processes
class Processes(threading.Thread):
    def run(self):
        while 1:
            fn = filejobs.get()
            p = Process(fn)
            p.process()
            filejobs.task_done()


class PMC2ES(object):

    def __init__(self):
        pass
                

    # do everything
    def do(self):
        if config.es_prep: self._prep_index() # prep the index if specified
        dirList = os.listdir(config.filedir) # list the contents of the directory where the source files are
        filecount = 0

        if config.threads:
            print "starting threaded processing"
            for x in xrange(config.threads):
                Processes().start()
            for i in dirList:
                filejobs.put(i)
            filejobs.join()

        else:
            for filename in dirList:
                filecount += 1
                if filecount >= config.startingfile: # skip ones already done by changing the > X
                    print filecount, config.filedir, filename
                    p = Process(filename)
                    p.process()


    # prep the index to receive files
    def _prep_index(self):
        # check ES is reachable
        test = 'http://' + str( config.es_url ).lstrip('http://').rstrip('/')
        try:
            hi = requests.get(test)
            if hi.status_code != 200:
                print "there is no elasticsearch index available at " + test + ". aborting."
                sys.exit()
        except:
            print "there is no elasticsearch index available at " + test + ". aborting."
            sys.exit()

        print "prepping the index"
        # delete the index if requested - leaves the database intact
        if config.es_delete_indextype:
            print "deleting the index type " + config.es_indextype
            d = requests.delete(config.es_target)
            print d.status_code

        # check to see if index exists - in which case it will have a mapping even if it is empty, create if not
        dbaddr = 'http://' + str( config.es_url ).lstrip('http://').rstrip('/') + '/' + config.es_index
        if requests.get(dbaddr + '/_mapping').status_code == 404:
            print "creating the index"
            c = requests.post(dbaddr)
            print c.status_code

        # check for mapping and create one if provided and does not already exist
        # this will automatically create the necessary index type if it is not already there
        if config.es_mapping:
            t = config.es_target + '_mapping' 
            if requests.get(t).status_code == 404:
                print "putting the index type mapping"
                p = requests.put(t, data=json.dumps(config.es_mapping) )
                print p.status_code


if __name__ == "__main__":
    from datetime import datetime
    started = datetime.now()
    print started
    parser = PMC2ES()
    parser.do()
    ended = datetime.now()
    print ended
    print ended - started
