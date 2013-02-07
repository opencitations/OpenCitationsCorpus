# Takes a folder full of NLM XML tar files and converts them to bibJSON
# Every <batchsize> records get batched up and send to an ES index
# Includes provision of all the data required for a BibServer to run on that index

# NOTE THIS HAS BEEN WRITTEN TO WORK ON THE FULL NLM MEDLINE DATA DUMP
# Probably needs tweaking for the purposes of running on the PMC OA data

# This does not yet raise errors or log progress

# This script MUST be able to write to disk in the area it runs

# For fitting this into a pipeline, we would need:
#   * code to get the raw files from the remote location into the filedir 
#     (or re-write the read_file to read remote accessible files)
#   * when running the parse_nlm_xml, a call-out when pulling citations to get more metadata for them
#   * to create records for those citations in the bibserver and get back their IDs
#   * to update the record with the citation ID (this can be calculated if enough is known about the citation)
#   * where the cited records have citations themselves, do the same for them

# A test run of this script on 36 of the raw Medline xml.tar.gz files - about half taken from the start (smaller) 
# and half from the end (much larger) - totalling 485MB whilst still compressed, standardly containing 30,000 records 
# for a total of 1,054,848 (the last file number 0684 only has 4848 records). All were indexed successfully.
# Core i5 laptop (2 threaded cores for a total of 4 vcores), 16GB RAM.
#
# Running this script as one thread serially across the files took 34 MINUTES. 
# used 100% of one CPU for most of that time.
#
# The same machine was running the ES index, and the indexing activities generated spikes of about 50% of one other CPU time. 
# RAM reserved for this script peaked at 5807MB, and for ES at 3486MB.
# Total max used by the machine (including other things it was doing) during the test was 10912MB. 
# ES can be configured to use Min / Max RAM amounts and also to lock the Max it may need, if necessary.
# The index remained responsive to queries throughout this period and required no downtime.
#
# The final size of the index on disk is 4.2gb. But I know from experience this does not mean the final index would be 20 times as large.
# There are already enough unique authors in a collection of this size to make faceting on authors noticably a bit slow.
#
# Of interest - the most cited pubmed article in this subset is http://www.ncbi.nlm.nih.gov/pubmed/18156677
# A short history of SHELX by GM Sheldrick, published 2008 Acta Crystallogr A.
# It was cited 6083 times in 2010 and 2011. It is open access.

# If you want to process your raw files faster, then the controller that calls this 
# script should batch the raw files into different folders, then call a version of the
# class in a subprocess for each folder, and set the filedir appropriately for each subprocess.
# Or we could write threading into this, have a method for splitting the file selections across 
# the processes. Just need to make sure that no thread tried to untar the already decompressed 
# file that another thread was working on - perhaps just write them into the directory above 
# whilst they are being operated on

from elementtree import ElementTree as ET
from datetime import datetime
import requests, json, os, gzip
import hashlib, md5, re
from unicodedata import normalize


class PMC2ES(object):

    # note when batching that NLM medline files come with 30000 records per file
    # you need enough memory to have the NLM XML file open and parsed, and enough for the temp store of records
    # batches will be sent at the end of each file, or on the last file, or when batch size is reached

    def __init__(self,
        # set the bibserver params you want, and other starting values for each bibJSON object
        # a bibjson url and identifier object will also be written in, so set params for them too
        bibjson_url = "http://bibsoup.net/record/",
        bibjson_collname = "opencitations", # the name of this collection, for bibsoup
        bibjson_creator = "occbulk", # the name of the creator of this record, for bibsoup
        include_abstracts = True, # They are copyright ambiguous for metadata - fine if your dataset is OA
        include_citations = True, # They are copyright ambiguous for metadata - fine if your dataset is OA
        keep_bulk_files = False, # keep the bulk files sent to the index on disk
        keep_batched_json = False, # keep the JSON batches created on disk
        bulk_load = True, # whether or not to bulk load the data to ES - this is a GOOD IDEA for any large dataset
        batchsize = 10000, # size of batches to bundle and send to the index. If zero, they will all be kept and done at the end
        filedir = './medline/', # where are the raw files?
        outdir = './pmc2es_output/', # where to write output files to?
        startingfile = 1, # to skip some files e.g. on re-run, set to the number of file to start on (note they are not processed in disk order)
        es_url = "localhost:9200", # where is the ES index?
        es_index = "test", # what is the name of the elasticsearch database to use?
        es_indextype = "record", # what is the name of the index object type to save into?
        es_prep = True, # prep the index by making sure it exists and sending it a mapping before doing any uploads
        es_delete_indextype = True, # wipe the specified index before starting. This only happens if prep is also true
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
    ):

        self.bibjson_url = bibjson_url
        self.bibjson_collname = bibjson_collname
        self.bibjson_creator = bibjson_creator
        self.include_abstracts = include_abstracts
        self.include_citations = include_citations
        self.keep_bulk_files = keep_bulk_files
        self.keep_batched_json = keep_batched_json
        self.bulk_load = bulk_load
        self.batchsize = batchsize
        self.filedir = filedir
        self.outdir = outdir
        self.startingfile = startingfile
        self.es_url = es_url
        self.es_index = es_index
        self.es_indextype = es_indextype
        self.es_prep = es_prep
        self.es_delete_indextype = es_delete_indextype
        self.es_mapping = es_mapping

        self.es_target = 'http://' + str( self.es_url ).lstrip('http://').rstrip('/')
        self.es_target += '/' + es_index.lstrip('/').rstrip('/') + '/' + es_indextype.lstrip('/').rstrip('/') + '/'
        
        if (self.keep_bulk_files or self.keep_batched_json) and not os.path.exists(self.outdir): os.makedirs(self.outdir)
                

    def makeid(self, data):
        # note this is a copy of the bibserver DAO record ID maker, found on line 172 of that file
        # you could also just import it instead of having it specified explicitly here
        id_data = {
            'author': [i.get('name','') for i in data.get('author',[])],
            'title': data.get('title',''),
            'identifier': [i.get('id','') for i in data.get('identifier',[]) if i.get('type','').lower() != "bibsoup"]
        }
        if id_data['author'] is not None: id_data['author'].sort() # these must be done after the comprehensions above or they give null
        if id_data['identifier'] is not None: id_data['identifier'].sort()
        buf = self.slugify(json.dumps(id_data, sort_keys=True).replace('author:','').replace('title:','').replace('identifier:','').replace('null','').decode('unicode-escape'),delim=u'')
        new_id = hashlib.md5(buf).hexdigest()
        return new_id

    # also copied from bibserver code, from the UTIL, for use in the make ID function
    def slugify(self, text, delim=u'_'):
        _punct_re = re.compile(r'[\t !"$%&\'()*\-/<=>?@\[\\\]^`{|},.]+')
        result = []
        for word in _punct_re.split(text.lower()):
            word = normalize('NFKD', word).encode('ascii', 'ignore')
            if word:
                result.append(word)
        return unicode(delim.join(result))


    # prep the index to receive files
    def prep_index(self):
        print "prepping the index"
        # delete the index if requested - leaves the database intact
        if self.es_delete_indextype:
            print "deleting the index type " + self.es_indextype
            requests.delete(self.es_target)

        # check to see if index exists - in which case it will have a mapping even if it is empty, create if not
        dbaddr = 'http://' + str( self.es_url ).lstrip('http://').rstrip('/') + '/' + self.es_index + '/_mapping'
        if requests.get(dbaddr).status_code == 404:
            print "creating the index"
            requests.post(dbaddr)

        # check for mapping and create one if provided and does not already exist
        # this will automatically create the necessary index type if it is not already there
        if self.es_mapping:
            t = self.es_target + '_mapping' 
            if requests.get(t).status_code == 404:
                print "putting the index type mapping"
                r = requests.put(t, data=json.dumps(self.es_mapping) )

    
    # read the source file, ready for conversion
    def read_file(self,filename):
        # read the tar file and unpack it to tar 
        tarobj = gzip.open(self.filedir + filename)
        outfile = open(self.filedir + filename.replace(".gz",""), 'w')
        outfile.write(tarobj.read())
        outfile.close()
        del tarobj

        # parse then delete the xml file
        # this causes delay and requires enough free memory to fit the file
        tree = ET.parse(self.filedir + filename.replace('.gz',''))
        elements = tree.getroot()
        os.remove(self.filedir + filename.replace(".gz",""))

        return elements


    def parse_nlm_xml(self,subelement):
        # parse the item into a dict, using some pre-defined details if available
        doc = {
            '_collection': [self.bibjson_creator + '_____' + self.bibjson_collname],
            '_created': datetime.now().strftime("%Y-%m-%d %H%M"),
            '_created_by': self.bibjson_creator
        }

        # look for the PMID
        try:
            if "identifier" not in doc: doc["identifier"] = []
            doc["identifier"].append({"type":"PMID","id":subelement.find("PMID").text})
        except:
            pass

        # look for any affiliations - not stricyly bibjson, but quite useful
        try:
            doc["affiliation"] = subelement.find("Affiliation").text
        except:
            pass

        # look for any keywords
        try:
            keywordlist = subelement.find("KeywordList")
            doc["keyword"] = []
            for keyword in keywordlist:
                doc["keyword"].append(keyword.text)
        except:
            pass

        # look for grant info - not strictly bibjson but may be useful
        try:
            grantlist = subelement.find("GrantList")
            doc["grant"] = []
            for grant in grantlist:
                doc["grant"].append({"agency":grant.find("Agency").text})
        except:
            pass

        # get the citations
        if self.include_citations:
            try:
                comments = subelement.find("CommentsCorrectionsList")
                doc["citation"] = []
                for comment in comments:
                    doc["citation"].append({
                        "identifier":[
                            {
                                "description":comment.find("RefSource").text,
                                "type": "PMID",
                                "id":comment.find("PMID").text
                            }
                        ]
                    })
            except:
                pass

        # identify the article object and set the title and language
        try:
            article = subelement.find("Article")
            doc["title"] = article.find("ArticleTitle").text
            doc["language"] = article.find("Language").text
        except:
            pass
        
        # look for abstracts if allowed
        if self.include_abstracts:
            # look for a generic record abstract
            try:
                otherabstract = subelement.find("OtherAbstract")
                doc["abstract"] = otherabstract.find("AbstractText").text
            except:
                pass

            # see if there is a specific article abstract
            try:
                abstract = article.find("Abstract")
                if abstract:
                    for item in abstract:
                        try:
                            doc["abstract"] = abstract.find("AbstractText").text
                        except:
                            pass
                        try:
                            doc["license"] = [{"description":abstract.find("CopyrightInformation").text}]
                        except:
                            pass
            except:
                pass
        
        # look for DOI
        try:
            doi = article.find("ELocationID")
            if doi.attrib["EIdType"] == "doi":
                if "identifier" not in doc: doc["identifier"] = []
                doc["identifier"].append({"type":"DOI","id":doi.text})
        except:
            pass
        
        # look for author list
        try:
            authorlist = article.find("AuthorList")
            doc["author"] = []
            for author in authorlist:
                lastname = author.find("LastName").text
                firstname = author.find("ForeName").text
                initials = author.find("Initials").text
                doc["author"].append({
                    "name": lastname + " " + firstname,
                    "lastname":lastname,
                    "firstname":firstname
                })
        except:
            pass

        # look for journal information
        try:
            journal = article.find("Journal")
            doc["journal"] = {
                "name":journal.find("Title").text,
                "identifier":[
                    {
                        "type": "issn",
                        "id": journal.find("ISSN").text
                    },
                    {
                        "type": "iso",
                        "id": journal.find("ISOAbbreviation").text
                    }
                ]
            }
            try:
                journalissue = journal.find("JournalIssue")
                doc["journal"]["volume"] = journalissue.find("Volume").text
            except:
                pass
            try:
                journalpubdate = journalissue.find("PubDate")
                doc["journal"]["year"] = journalpubdate.find("Year").text
                doc["journal"]["month"] = journalpubdate.find("Month").text
            except:
                pass
        except:
            pass
                    
        # look for dates
        try:
            articledate = article.find("ArticleDate")
            doc["year"] = articledate.find("Year").text
            doc["month"] = articledate.find("Month").text
            doc["day"] = articledate.find("Day").text
        except:
            pass
        
        # give this record an _id and subsequently a URL and bibsoup identifier
        doc['_id'] = self.makeid(doc)
        if "identifier" not in doc: doc["identifier"] = []
        doc["url"] = self.bibjson_url + doc["_id"]
        doc["identifier"].append({"type":"bibsoup","id":doc["_id"],"url":doc["url"]})
        
        # return the record
        return doc


    def es_load_record(self,record):
        r = requests.post(self.es_target + record['_id'], data=json.dumps(record))
        return r


    def es_bulk_load(self,recs,bulkfilename):
        # http://www.elasticsearch.org/guide/reference/api/bulk.html        
        data = ''
        for r in recs:
            data += json.dumps( {'index':{'_id':r['_id']}} ) + '\n'
            data += json.dumps( r ) + '\n'
        r = requests.post(self.es_target + '_bulk', data=data)
        print r.status_code

        if self.keep_bulk_files:
            bulker = open(bulkfilename,'w')
            bulker.write(data)
            bulker.close()

        return r # passing back the POST info in case it is useful


    # do everything
    def do(self):
        if self.es_prep: self.prep_index() # prep the index if specified
        
        dirList = os.listdir(self.filedir)
        temp_records = []
        filecount = 0
        for filename in dirList:
            filecount += 1
            if filecount >= self.startingfile: # skip ones already done by changing the > X
                print filecount, self.filedir, filename
                                
                # read the XML file
                elements = self.read_file(filename)

                # for every item in the xml file, parse it and create a bibJSON object of it
                recordcount = 0
                for sub in elements:
                    recordcount += 1
                    
                    # parse the XML to JSON and stick it in the temp store
                    doc = self.parse_nlm_xml(sub)
                    temp_records.append( doc ) 

                    # If batching is enabled by setting a batchsize and temp store has reached it, 
                    # or batching is enabled but we have reached the end of this file, 
                    # or we have reached the end of the last file (whether batching or not)
                    if (self.batchsize and (len(temp_records) == self.batchsize)) or (self.batchsize and recordcount == len(elements)) or (filecount == len(dirList) and recordcount == len(elements)):
                        bulk_filename = self.outdir + 'conversion_records_bulk_' + str(filecount) + '_' + str(recordcount) + '.json'
                        print "sending batch " + bulk_filename
                        if self.bulk_load:
                            self.es_bulk_load(temp_records, bulk_filename) # bulk load the temp store to ES - a GOOD IDEA
                        else:
                            for rec in temp_records: self.es_load_record(record) # load each record individually

                        # if you want to keep the JSON records that were created in batches, save them to file
                        if self.keep_batched_json:
                            json_filename = bulk_filename.replace('_bulk_','_json_')
                            jsons = open(json_filename,'w')
                            jsons.write( json.dumps( temp_records, indent=4 ) )
                            jsons.close()

                        # now wipe the temp records for the next loop
                        temp_records = []

                print recordcount


if __name__ == "__main__":
    # TODO: add a bit here to take sysargs, if that would be useful
    parser = PMC2ES()
    parser.do()

