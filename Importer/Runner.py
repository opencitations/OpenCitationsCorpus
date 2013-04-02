#!/usr/bin/env python
# encoding: utf-8
"""
Runner.py

Created by Martyn Whitwell on 2013-02-08.

to run, you will need the following Python libraries
pip install python-dateutil
pip install pyoai
pip install lxml (and probably libxslt2-dev and libxml on your machine)
pip install -U requests #Upgrades to the latest version of requests

"""

import sys
import os
import argparse
import OpenCitationsImportLibrary


def main(action, source, identifier):
    print "OPEN CITATIONS IMPORTER"
    #print "-----------------------"
    if (action=="load"):
        if (source=="pubmedcentral"):
            print "Loading %s" % (source)
            if (identifier is not None):
                print "Warning: identifier option (%s) is ignored during the load operation" % (identifier)
        else:
            print "Unfortunately, only data sourced from pubmedcentral can be loaded at present.\nFor other sources, try to synchronise instead."

    elif (action=="synchronise"):
        if (identifier is None):
            print "Synchronising %s" % (source)

        else:
            print "Synchronising %s for identifier:%s" % (source, identifier)


    else:
        print "Unknown action: %s" % action
        
        

    #os.system('clear')
    #print "OPEN CITATIONS IMPORTER: %s on %s for id %s" % (action, source, id)


    #arxiv = OpenCitationsImportLibrary.OAIImporter("http://export.arxiv.org/oai2", 0, OpenCitationsImportLibrary.OAIImporter.METADATA_FORMAT_ARXIV)
    #arxiv.run()
    
    #pmc_oa = OpenCitationsImportLibrary.OAIImporter("http://www.pubmedcentral.nih.gov/oai/oai.cgi", 0, OpenCitationsImportLibrary.OAIImporter.METADATA_FORMAT_PMC)
    #pmc_oa.run()


    #d = Downloader.DownloadArXiv()
    #d.bibify_with_tex2bib()
    #d.load_citations()

    #pmc_parser = OpenCitationsImportLibrary.PMCBulkImporter()
    #pmc_parser.do()



    print "Finished."
    pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Open Citations Importer')
    parser.add_argument("-a", "--action", required=True, choices=["load", "synchronise"], help="Importer action to perform either: load or synchronise")
    parser.add_argument("-s", "--source", required=True, choices=["pubmedcentral", "arxiv"], help="Source either: pubmedcentral or arxiv")
    parser.add_argument("-i", "--id", required=False, help="Synchronise only the record specified by the given identifier")
    args = parser.parse_args()
    
    main(args.action, args.source, args.id)
