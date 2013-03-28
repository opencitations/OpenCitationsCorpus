Open Citations Importer
=======================

2013-03-28

Authors: Mark MacGillivray, Martyn Whitwell, Heinrich Hartmann, Alex Dutton

This repository contains code for the Open Citations Importer. It is based on
earlier work by Dr Heinrich Hartmann (OAI reader), Alex Dutton (PubMedCentral
reader) and Mark MacGillivray (PubMedCentral reader).


Status
------

This code is in testing and is still being developed and improved.


Open Citations Index
--------------------

The Open Citations Index is an ElasticSearch index containing metadata about
articles (including books, chapters and reports etc) and the citation
relationships between the articles. It is currently populated from two
sources: the PubMedCentral Open Access Subset
(http://www.ncbi.nlm.nih.gov/pmc/tools/openftlist/) and the arXiv repository
(http://arxiv.org).


Importer
--------

The importer can operate in two different modes: as a bulk loader and also as
an OAI-PMH feed synchroniser. The bulk loader is only suitable for running on
PubMedCentral OA data, and will quickly build a near-complete index of
PubMedCentral OA records. The OAI-PMH synchroniser is designed to be run as a
scheduled job (e.g. via cron) to keep the index up-to-date, and will work on both the PubMedCentral OA and arXiv OAI-PMH feeds.


Code
----

The project consists of five core modules:

* Runner.py - command line interface to the importer
* OpenCitationsImportLibrary.py - key code to import article metadata and
  citations from sources and synchronise with the Open Citations Index
* MetadataReaders.py - libraries to parse arXiv and PubMedCentral metadata,
  and also tex files and extract citations.
* Matcher.py - library to match citations with existing articles in the Open
  Citations Index
* Config.py - configuration settings


Setup
-----
Instructions subject to change - this section will be expanded on shortly.

To run the Open Citations Importer:

1. Download, install and run elasticsearch:
   http://www.elasticsearch.org/download/
2. Download this code and update the values in Config.py to suit your setup
3. Execute Runner.py from the commandline, specifying the COMMAND and the
   SOURCE
