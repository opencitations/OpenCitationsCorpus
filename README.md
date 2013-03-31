Open Citations Corpus Datastore
===============================

This repository contains code for the Open Citations Corpus Datastore (OCCD). 

It consists of several parts:
* PMC import scripts
* Arxiv import scripts
* OCCD server (tbd)
  

Installing
----------

You will need python, and git to clone this repo (or just download it).
This code depends on lxml so you will need that installed.
You will also need a running instance of elasticsearch to load into. 
It is easy to install. See the elasticsearch website.
Creating a virtualenv is a good idea too.

Here is an example install: 

    apt-get install libxslt2-dev libxml
    virtualenv -p python2.7 occ --no-site-packages
    cd occ
    mkdir src
    cd src
    git clone https://github.com/opencitations/OpenCitationsCorpus.git

To then go on and create an index, make sure your elasticsearch index is running then 
edit the Importer/Config.py file to point at the relevant index address. Check out the 
other settings whilst there too. It will all work by default as long as you have your 
index running on the usual port, and also if you grab the bulk files available from PMC OA
ftp site and put them in a directory called pmcoa inside Importer. Then create a directory 
called workdir in Importer too, which will be used for unpacking and processing files. The 
default also wipes any index already existing at the usual address named "occ", so change 
that in the config if you don't want to call it that, or set "prep_index" to false if you 
don't want it wiped.

Then do this to build a new index from scratch out of PMC OA bulk ftp files:

    cd OpenCitationsCorpus
    pip install -e .
    cd Importer
    python OpenCitationsImportLibrary.py
    
    
A complete rebuild will take a few hours to run.


Status
------

David is working on the datastructures for the CCD server, and the
mappings from the existing PMC/Arxiv data fields. As soon as this in
done we can

* adapt the import scripts to the new format
* work with relyable data in the front end
* strat implementing the CCD.


Pipeline
--------

Mark has added a pipeline folder with a first python file


BibServer
---------

Mark has added bibserver as a submodule. After cloning this repo, do 
git submodule update --init --recursive
to have a working repo.
