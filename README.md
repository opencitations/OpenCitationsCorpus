Open Citations Corpus Datastore
===============================

This repository contains code for the Open Citations Corpus Datastore (OCCD). 

It consists of several parts:
* PMC import scripts
* Arxiv import scripts
* OCCD server (tbd)
  

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
