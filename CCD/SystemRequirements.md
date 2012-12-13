System requirements CitationCorpusDatastore
===========================================

Current dataset consitst of:

* ~ 1.1m genuine articles (harvested from arXiv/PMC)
* > 20m citation targets
* > 800.000 Author names

To be safe for the near future, our system should be able to handle:

* 10m articles
* 100m citation targets
* 4m author names


Services provided by the CCD
----------------------------
* Lookup of author/paper records given an ID (e.g. internal, Arxiv, PMC, DOI)
* Bulk export of the whole dataset in XML/RDF
* Add new articles 
* Update/Merge existing articles manually

Remarks:

* Searching for titles/authors is a front-end feature, which the CCD
  does not need to offer as a service.

To support this functions the datastore need to hande the following tasks well:

* Add new document to the sore
* Remove documents from the store
* Updating single fields inside a document
* Fast lookup of DOI/ArxivId/... (currently in memory hash map)

Internal tasks
--------------
* Metadata augmentation of citation targets
* Merging of citation targets
* Manage author identieties (merge)

To support this functions the datastore need to hande the following tasks well:

* Add fields to an existing document
* Find similar citation targets (currently done via DOI extraction)


Relieability constrains
-----------------------

* Computers may crash: We need to make sure, we recover
  to a consistent state within the last 24h, within a 
  barable amount of time.
  
