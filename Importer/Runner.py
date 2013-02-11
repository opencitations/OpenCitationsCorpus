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
	#arxiv = OpenCitationsImportLibrary.OAIImporter("http://export.arxiv.org/oai2", "2012-01-02", "2012-01-03")
	#arxiv.run()
	
	pmc_oa = OpenCitationsImportLibrary.OAIImporter("http://www.pubmedcentral.nih.gov/oai/oai.cgi", 
		"2012-01-02", "2012-01-03", 1, OpenCitationsImportLibrary.OAIImporter.METADATA_PREFIX_PMC_FM)
	pmc_oa.run()

	pass


if __name__ == '__main__':
	main()
