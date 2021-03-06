# Need to import MetadataReaders to reference them later on in the Config
import MetadataReaders



# set the bibserver params you want, and other starting values for each bibJSON object
# a bibjson url and identifier object will also be written in, so set params for them too
# NO DATA GETS SENT DIRECT TO THIS BIBSERVER - IT IS JUST USED TO WRITE THE RECORDS SO THEY WOULD BE SUITABLE FOR IT
bibjson_url = "http://bibsoup.net/record/"
bibjson_collname = "opencitations" # the name of this collection, for bibsoup
bibjson_creator = "occ" # the name of the creator of this record for bibsoup


elasticsearch = {
    "batchsize": 5000, # size of batches to bundle and send to the index. If zero they will all be kept and done at the end.
    "uri_base": "http://localhost:9200", # where is the ES index?
    "index": "occ", # what is the name of the elasticsearch database to use?
    "type_record": "record",  # what is the name of the index object type to save into?
    "type_config": "config",
    "mapping": { # the mapping to use for the ES index - this one here is the default record mapping for bibserver
        "record" : {
            "dynamic_templates" : [
                {
                    "default" : {
                        "match" : "*",
                        "match_mapping_type": "string",
                        "mapping" : {
                            "type" : "multi_field",
                            "fields" : {
                                "{name}" : {"type" : "{dynamic_type}", "index" : "analyzed", "store" : "no"},
                                "exact" : {"type" : "{dynamic_type}", "index" : "not_analyzed", "store" : "yes"}
                            }
                        }
                    }
                }
            ],
            "properties":{
                "date":{
                    "type": "date",
                    "index": "not_analyzed",
                    "format": "dd/MM/yyyy"
                }
            }
        }
    }
}
elasticsearch['uri_index'] = elasticsearch['uri_base'].rstrip('/') + '/' + elasticsearch['index'] + '/'
elasticsearch['uri_records'] = elasticsearch['uri_index'] + elasticsearch['type_record'] + '/'
elasticsearch['uri_configs'] = elasticsearch['uri_index'] + elasticsearch['type_config'] + '/'



importer = {
    "load" : {
        "arxiv": {
            "name": "arXiv Tar Files",
            "filedir": "./DATA/arXiv/source/",
            "workdir": "./DATA/arXiv/workdir/",
            "metadata_reader": MetadataReaders.CitationExtractorTex()
        },
        "pubmedcentral" : {
            "name": "PubMedCentral Open Access Files",
            "filedir": './pmcoa/',
            "workdir": './workdir/',
            "threads": 0,
            "startingfile": 1,
            "do_bulk_match": False,
            "skip_tar": False
        }
    },
    "synchronise" : {
        "arxiv": {
            "name": "arXiv OAI-PMH",
            "uri": "http://export.arxiv.org/oai2",
            "metadata_format": "arXiv",
            "metadata_reader": MetadataReaders.MetadataReaderArXiv(),
            "delta_days": 1, #synchronise 1 day at a time
            "default_from_date": "2000-01-01"
        },
        "pubmedcentral" : {
            "name": "PubMedCentral Open Access OAI-PMH",
            "uri": "http://www.pubmedcentral.nih.gov/oai/oai.cgi",
            "metadata_format": "pmc",  #pmc includes full text for a small subset of the PubMedCentral open access set. Otherwise use pmc_fm to get basic metadata (excluding citations)
            "metadata_reader": MetadataReaders.MetadataReaderPMC(),
            "delta_days": 1, #synchronise 1 day at a time
            "default_from_date": "2000-01-01"
        }
    }
}


# ----------------------------------------- OLD SETTINGS --------------------
# MW: 2013-04-14
# THESE CONFIGURATION OPTIONS ARE DEFUNCT 
# See the importer definition above instead

# set threads to a number of threads to run. Note you need enough disk and RAM to support them all
# and there is little point if you don't have enough processors to run them
# leave as zero if you don't want threading
#threads = 0
# note when batching that NLM medline files come with 30000 records per file
# you need enough memory to have the NLM XML file open and parsed, and enough for the temp store of records
#batchsize = 5000 # size of batches to bundle and send to the index. If zero they will all be kept and done at the end.
#filedir = './pmcoa/'
#workdir = './workdir/'
#filedir = '../../../contracting/cottage/open citations/early_code/pmcoa/' # where are the raw files? trailing slash required
#workdir = '../../../contracting/cottage/open citations/early_code/workdir/' # a directory into which files can be uncompressed temporarily (will actually be affixed with a uuid)

# to skip some files e.g. on re-run set to the number of file to start on
# note files are not processed in folder display order - so this is only good if you know the file number
# that a previous loop failed on. And it is no use for threaded processing
#startingfile = 1 

# if this is set it is assumed you already have a workdir with some folders full of uncompressed files ready to process
#skip_tar = False

# if this is true matching will be performed on every record after a bulk load
#do_bulk_match = False


#es_url = "localhost:9200" # where is the ES index?
#es_index = "occ" # what is the name of the elasticsearch database to use?
#es_indextype = "record" # what is the name of the index object type to save into?
#es_synchroniser_config_type = 'synchroniser_config'

#es_target = 'http://' + str( es_url ).lstrip('http://').rstrip('/')
#es_target += '/' + es_index.lstrip('/').rstrip('/') + '/' + es_indextype.lstrip('/').rstrip('/') + '/'

#es_synchroniser_config_target = 'http://' + str( es_url ).lstrip('http://').rstrip('/')
#es_synchroniser_config_target += '/' + es_index.lstrip('/').rstrip('/') + '/' + es_synchroniser_config_type.lstrip('/').rstrip('/') + '/'

#es_prep = True # prep the index by making sure it exists and sending it a mapping before doing any uploads
#es_delete_indextype = True # wipe the specified index before starting. This only happens if prep is also true
