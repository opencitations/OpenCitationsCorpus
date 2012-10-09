PubMed Open Access transformation to RDF
========================================

This repository contains scripts used to transform the NLM XML available at
the `National Library of Medicine's FTP site <ftp://ftp.ncbi.nlm.nih.gov/pub/pmc/>`_ into RDF.

Process
-------

Convert each of the NLM XML files to an intermediate XML representation using e.g.::

   $ ./transform.sh article-data.xsl data/AAPS_J/AAPS_J-10-1-2747081.nxml > out/AAPS_J/AAPS_J-10-1-2747081.nxml.xml

It is recommended that you do this with some sort of for loop. 

Next, cd into pubmed and do run::

   $ mkdir -p ../parsed/
   $ python bibjson_parse.py

This will create ``parsed/articles-raw.bibjson.tar.gz``, a tarball of BibJSON files, one per article XML file.

Then run, in order::

   $ python bibjson_augment.py # Queries the NLM API for more details about (non-OA) referenced articles
   $ python bibjson_sanitize.py 
   $ python bibjson_unify.py

Finally, generate some n-triples::

   $ python bibjson_rdf.py > nlm.nt


