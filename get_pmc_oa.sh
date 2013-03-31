#! /bin/bash

cd Importer
mkdir pmcoa
cd pmcoa

wget ftp://ftp.ncbi.nlm.nih.gov/pub/pmc/articles.A-B.tar.gz
wget ftp://ftp.ncbi.nlm.nih.gov/pub/pmc/articles.C-H.tar.gz
wget ftp://ftp.ncbi.nlm.nih.gov/pub/pmc/articles.I-N.tar.gz
wget ftp://ftp.ncbi.nlm.nih.gov/pub/pmc/articles.O-Z.tar.gz

cd ../../
