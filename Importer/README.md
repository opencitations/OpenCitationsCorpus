Open Citations Importer
=======================

2013-03-28

Authors: Mark MacGillivray, Martyn Whitwell, Heinrich Hartmann

This repository contains code for the Open Citations Importer. It is based on
earlier work by Dr Heinrich Hartmann (OAI reader), Alex Dutton (PubMedCentral
reader), Mark MacGillivray (PubMedCentral reader) and Dr David Shotton


Status
------

This code is in testing and is still being developed and improved. Your
mileage may vary!


Open Citations Index
--------------------

The Open Citations Index is an ElasticSearch index containing metadata about
articles (including books, chapters and reports etc) and the citation
relationships between the articles. It is currently populated from two
sources: the [PubMedCentral Open Access Subset](http://www.ncbi.nlm.nih.gov/pmc/tools/openftlist/) 
and the [ArXiv repository](http://arxiv.org).


Importer
--------

The importer can operate in two different modes: as a bulk loader and also as
an OAI-PMH feed synchroniser. The bulk loader is only suitable for running on
PubMedCentral OA data, and will quickly build a near-complete index of
PubMedCentral OA records. The OAI-PMH synchroniser is designed to be run as a
scheduled job (e.g. via cron) to keep the index up-to-date, and will work on 
both the PubMedCentral OA and arXiv OAI-PMH feeds.


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
* Batch.py - library to batch requests to elasticsearch together, to improve
  performance


Setup
-----

To run the Open Citations Importer:

1. Download, install and run [ElasticSearch](http://www.elasticsearch.org/download/)
2. Download this code from [GitHub](https://github.com/opencitations/OpenCitationsCorpus.git)
3. Configure settings and the values in `Config.py` to suit your setup. The
   default settings are probably fine for most users, although you may want to
   change file paths or the location of the elasticsearch server
4. Execute `Runner.py` from the command-line, specifying the *Action* and the
   *Source* parameters. See Usage below for the recommended approach for bulk
   loading and synchronising.

   For example, to synchronise with the arXiv source via the OAI-PMH feed,
   run:

   `$ python Runner.py --action synchronise --source arxiv`

   Or, to synchronise with the PubMedCentral source via the OAI-PMH feed for
   records updated in the first three days of August 2009, run:

   `$ python Runner.py --action synchronise --source pubmedcentral --from 2009-08-01 --to 2009-08-03`

   Or, to rebuild (drop and recreate) the index and then bulk-load the
   PubMedCentral Open Access files, run:

   `$ python Runner.py --action load --source pubmedcentral --REBUILD`

   Or, to synchronise a specific record (`id=3625889`) from PubMedCentral, run:

   `$ python Runner.py --action synchronise --source pubmedcentral --id oai:pubmedcentral.nih.gov:3625889`

   Or, to synchronise a specific record (`id=1209.0458`) from arXiv, run:

   `$ python Runner.py --action synchronise --source arxiv --id oai:arXiv.org:1209.0458`

   For full list of command options, run:

   `$ python Runner.py --help`


Usage
-------

Open Citations Importer is designed to run along the following lines:

**PubMedCentral Open Access**

NB: The bulk load assumes an empty index. Once the bulk load has run, it
should **not** be run again.

1. Bulk load the PubMedCentral OpenAccess articles. The user will need to 
   download these files from [PubMedCentral's FTP servers](http://www.ncbi.nlm.nih.gov/pmc/tools/ftp/)
   prior to running the bulk load. Run the bulk load on an empty index (i.e.
   with the `--REBUILD` flag set)
2. Once the bulk load has been completed, the system can update itself on a
   daily basis via the *synchronise* action. When synchronising for the first
   time, use the `--from` flag to match the date where the bulk load ends.
   Synchronise can the run on a schedule (e.g. via `cron`). Note that it will
   remember the last point it synchronised too, so there is no need to set
   `--from` in the `cron` job.


**ArXiv**

NB: The ArXiv importer requires the system to synchronise fully with the ArXiv
feed, *and then* perform a bulk load of citations. This is the reverse order
as for PubMedCentral!

1. Synchronise ArXiv. The system typically synchronises at a rate of around 10
   records/second, so to synchronise the entire ArXiv repository will take a few
   days. For testing purposes, you can choose a smaller set - e.g. from 2013
   onwards, by specifying the `--from` option.
2. Once synchronised, configure your access to Amazon S3 (see `../ImportArxiv/tools/s3cmd/README`).
   Note that connecting and downloading data from Amazon S3 will incur charges
   and you can expect to spend around $50 if you download the entire arXiv
   archive (several hundred gigabytes). If you can obtain a recent version of
   the arxiv archive from another source, you will save yourself time and
   money. For more information see [arXiv Bulk Data Access - Amazon S3](http://arxiv.org/help/bulk_data_s3).
   Now run the bulk loader for arXiv. It will connect to Amazon S3 and download
   the source tar files specified in the `./DATA/arXiv/source/arXiv_s3_downloads.txt`
   file (NB: if you don't want to download anything, just make a blank file).
   Once downloaded, it will extract the tar files, expand the .gz files, mine
   .tex and .bbl source files and then update existing records in the Open
   Citations Index (which is why it is necessary to synchronise first, as 
   otherwise there will be nothing to update).

