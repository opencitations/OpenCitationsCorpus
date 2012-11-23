PubMedCentral Open Access transformation to RDF
===============================================

The following scripts transform the Meta- and Citationdata from the
OpenAccess subset of PubMedCentral to the RDF/XML format used in the
CitationCorpus.

These scripts were initially written by Alex Dutton.

Process
-------
1. Download raw data
   The raw data is available from the
   [PMC ftp server](https://www.ncbi.nlm.nih.gov/pmc/tools/ftp/#XML_for_Data_Mining)
   Extract the files `articles.A-B.tar.gz`, etc to the subdirectory `data/`

2. XML conversion 
   Convert each of the NLM XML files to an intermediate XML representation using

    $ ./transform.sh article-data.xsl data/AAPS_J/AAPS_J-10-1-2747081.nxml > out/AAPS_J/AAPS_J-10-1-2747081.nxml.xml

   It is recommended that you do this with some sort of for loop. 
 
   This script relies on the Apache XML Project (now Xerces) and the Saxon Java Library. 
   Download the files
   [xml-commons-resolover-1.2](http://www.mirrorservice.org/sites/ftp.apache.org//xerces/xml-commons/xml-commons-resolver-1.2.tar.gz)
   [saxon](http://sourceforge.net/projects/saxon/files/latest/download)
   extract them in your favorite directory, and alter the path in transform.sh accordingly.


3. BibJSON conversion
   Next, cd into pubmed and do run::
   
    $ mkdir -p ../parsed/
    $ python bibjson_parse.py

   This will create ``parsed/articles-raw.bibjson.tar.gz``, a tarball
   of BibJSON files (one per article XML file).

4. Data Cleanup  
   Query the NLM API for more details about (non-OA) referenced articles
    $ python bibjson_augment.py 

   Cleanup markup errors
    $ python bibjson_sanitize.py 
   
   Cluster citation targets
    $ python bibjson_unify.py

5. RDF Export
   Finally, generate n-triples::
   
    $ python bibjson_rdf.py > nlm.nt
    
