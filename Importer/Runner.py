#!/usr/bin/env python
# encoding: utf-8
"""
Runner.py

Created by Martyn Whitwell on 2013-02-08.

"""

import sys
import os
import OpenCitationsImportLibrary


def main():
    os.system('clear')
    print "OPEN CITATIONS IMPORTER"

    #arxiv = OpenCitationsImportLibrary.OAIImporter("http://export.arxiv.org/oai2", 0, OpenCitationsImportLibrary.OAIImporter.METADATA_FORMAT_ARXIV)
    #arxiv.run()
    
    pmc_oa = OpenCitationsImportLibrary.OAIImporter("http://www.pubmedcentral.nih.gov/oai/oai.cgi", 0, OpenCitationsImportLibrary.OAIImporter.METADATA_FORMAT_PMC)
    pmc_oa.run()

    print "Finished."
    pass


if __name__ == '__main__':
    main()

