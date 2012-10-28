# Data import scripts

This directory contains scripts to download data from arxiv (and
pubmed) and produces a neo4j db as ultimate output which contains meta
and reference information about all stored papers.

# Contents

* MetaImport -- imports metadata from arxiv
* Pubmed -- extract metadata and references from pubmed central xml files (under construction)
* BucketControl -- download full tex-sources from Amazon S3
* RefExtract -- extract references strings from tex-sources
* Matching -- match reference strings against metadatabase
* MapReduce -- automate reference extraction and matching
* Neo4J -- Create Neo4j database from reference and meta data
* DemoApp -- simple python webserver to display data


# Workflow

1. Download metadata using MetaImport/MetaHarvester.py
2. Create meta db's using MetaImport/MetaExport.py
3. Download source files using BucketControl/bucket_download.py
4. Extract source files using BucketControl/bucket_extract.py
5. Batch extract references using MapReduce/mapper.py and MapReduce/reduce.py
6. Match references to meta db using Matching/MatchScript.py
7. Create neo4j db using Neo4J/create_db.py

### Apology

    This process is obviously way more complicated than it needs to
    be.  Part of the complexity overhead is due to my experiments with
    e.g. multiprocessing techonologies, furthermore the scripts
    evolved over a period of a month or so gradually transforming the
    data.

    On the plus side, I tried to keep the individual scripts as simple
    as possible and write good documentation. I hope to streamline the
    workflow as the integration of other data sources comes along.
    