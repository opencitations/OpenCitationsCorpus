# set threads to a number of threads to run. Note you need enough disk and RAM to support them all
# and there is little point if you don't have enough processors to run them
# leave as zero if you don't want threading
threads = 4

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
batchsize = 5000 # size of batches to bundle and send to the index. If zero they will all be kept and done at the end.


es_url = "localhost:9200" # where is the ES index?
es_index = "test" # what is the name of the elasticsearch database to use?
es_indextype = "record" # what is the name of the index object type to save into?
es_synchroniser_config_type = 'synchroniser_config'

es_target = 'http://' + str( es_url ).lstrip('http://').rstrip('/')
es_target += '/' + es_index.lstrip('/').rstrip('/') + '/' + es_indextype.lstrip('/').rstrip('/') + '/'

es_synchroniser_config_target = 'http://' + str( es_url ).lstrip('http://').rstrip('/')
es_synchroniser_config_target += '/' + es_index.lstrip('/').rstrip('/') + '/' + es_synchroniser_config_type.lstrip('/').rstrip('/') + '/'

es_prep = False # prep the index by making sure it exists and sending it a mapping before doing any uploads
es_delete_indextype = True # wipe the specified index before starting. This only happens if prep is also true

es_mapping = { # the mapping to use for the ES index - this one here is the default record mapping for bibserver
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
                "index": "not_analyzed"#,
                #"format": "dd/MM/yyyy"
            },
           "_oaipmh_identifier":{
                "type": "string",
                 "index": "not_analyzed",
                 "include_in_all": True,
                 "store": "yes"},
           "_oaipmh_datestamp":{
                "type": "date",
                 "index": "not_analyzed",
                 "include_in_all": True,
                 "store": "yes"}

        }
    }
}

