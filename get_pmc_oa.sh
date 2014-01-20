#!/bin/bash

# stop script if something goes wrong
set -e

mkdir -p Importer/pmcoa
cd Importer/pmcoa

wget ftp://ftp.ncbi.nlm.nih.gov/pub/pmc/articles.A-B.tar.gz
wget ftp://ftp.ncbi.nlm.nih.gov/pub/pmc/articles.C-H.tar.gz
wget ftp://ftp.ncbi.nlm.nih.gov/pub/pmc/articles.I-N.tar.gz
wget ftp://ftp.ncbi.nlm.nih.gov/pub/pmc/articles.O-Z.tar.gz

