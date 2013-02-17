
# set whether to parse pmcoa subset tar.gz files or nlm medline xml.gz files
sourcetype = "pmcoa" # this should be pmcoa or nlm

# set this to bibserver if you want to use the bibserver hashing algorithm for IDs, otherwise set to uuid
idtype = "uuid"

# set threads to a number of threads to run. Note you need enough disk and RAM to support them all
# and there is little point if you don't have enough processors to run them
# leave as zero if you don't want threading
threads = 0

# set the bibserver params you want, and other starting values for each bibJSON object
# a bibjson url and identifier object will also be written in, so set params for them too
# NO DATA GETS SENT DIRECT TO THIS BIBSERVER - IT IS JUST USED TO WRITE THE RECORDS SO THEY WOULD BE SUITABLE FOR IT
bibjson_url = "http://bibsoup.net/record/"
bibjson_collname = "opencitations" # the name of this collection, for bibsoup
bibjson_creator = "occ" # the name of the creator of this record for bibsoup

include_abstracts = True # They are copyright ambiguous for metadata - fine if your dataset is OA
include_citations = True # They are copyright ambiguous for metadata - fine if your dataset is OA

# note when batching that NLM medline files come with 30000 records per file
# you need enough memory to have the NLM XML file open and parsed, and enough for the temp store of records
batchsize = 10000 # size of batches to bundle and send to the index. If zero they will all be kept and done at the end.
filedir = './pmcoa/' # where are the raw files? trailing slash required
workdir = './workdir/' # a directory into which files can be uncompressed temporarily (will actually be affixed with a uuid)

# to skip some files e.g. on re-run set to the number of file to start on
# note files are not processed in folder display order - so this is only good if you know the file number
# that a previous loop failed on. And it is no use for threaded processing
startingfile = 1 

es_url = "localhost:9200" # where is the ES index?
es_index = "test" # what is the name of the elasticsearch database to use?
es_indextype = "record" # what is the name of the index object type to save into?

es_target = 'http://' + str( es_url ).lstrip('http://').rstrip('/')
es_target += '/' + es_index.lstrip('/').rstrip('/') + '/' + es_indextype.lstrip('/').rstrip('/') + '/'

es_prep = True # prep the index by making sure it exists and sending it a mapping before doing any uploads
es_delete_indextype = True # wipe the specified index before starting. This only happens if prep is also true

es_mapping = { # the mapping to use for the ES index - this one here is the default record mapping for bibserver
    "record" : {
        "date_detection" : False,
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
        ]
    }
}

