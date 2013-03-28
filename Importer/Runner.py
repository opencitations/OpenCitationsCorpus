#!/usr/bin/env python
# encoding: utf-8
"""
Runner.py

Created by Martyn Whitwell on 2013-02-08.

"""

#import sys
import os
import argparse
#import OpenCitationsImportLibrary


def main(command, source):
    os.system('clear')
    print "OPEN CITATIONS IMPORTER: %s on %s" % (command, source)


    #arxiv = OpenCitationsImportLibrary.OAIImporter("http://export.arxiv.org/oai2", 0, OpenCitationsImportLibrary.OAIImporter.METADATA_FORMAT_ARXIV)
    #arxiv.run()
    
    #pmc_oa = OpenCitationsImportLibrary.OAIImporter("http://www.pubmedcentral.nih.gov/oai/oai.cgi", 0, OpenCitationsImportLibrary.OAIImporter.METADATA_FORMAT_PMC)
    #pmc_oa.run()


    #d = Downloader.DownloadArXiv()
    #d.bibify_with_tex2bib()
    #d.load_citations()

    #pmc_parser = OpenCitationsImportLibrary.PMCBulkImporter()
    #pmc_parser.do()



    print "Finished"
    pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("command", help="Importer action to perform either: BULKLOAD or SYNCHRONISE")
    parser.add_argument("source", help="Source either: PMCOA or ARXIV")
    args = parser.parse_args()
    main(args.command.lower(), args.source.lower())

