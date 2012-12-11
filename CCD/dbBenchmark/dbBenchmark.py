import string
import random
import pyes

import httplib
import json

class dbBenchmark():
    """
    Class for dbBenchmarking
    
    Benchmarks:
    * insert records
    * update records

    * Lookup ID
    * Search querry
    
    * Crash test
      kill on write
      recovery consistence
      
    Measure: Time/RAM/HDD
    """

    # dbConnection
    dbCon = None
    IDs = set([])

    def __init__(self):
        print "Setup db connections"
        
        # init db connections
        self.host = "localhost:9200"
        self.dbCon = pyes.ES(self.host)
        
        # reset index
        self.index_name = "bibserver-test"
        try:
            self.dbCon.indices.delete_index(self.index_name)
        except pyes.exceptions.IndexMissingException:
            pass

        self.dbCon.indices.create_index(self.index_name)
        
        # put mapping
        self.mapping_name = "record"
        fullpath = '/' + self.index_name + '/' + self.mapping_name + '/_mapping'
        c =  httplib.HTTPConnection(self.host)
        c.request('GET', fullpath)
        result = c.getresponse()
        if result.status == 404:
            print self.mapping_name
            c =  httplib.HTTPConnection(self.host)
            c.request('PUT', fullpath, json.dumps(mappings[self.mapping_name]))
            res = c.getresponse()
            print res.read()
            
        print "Insert example record"

        # insert test example 
        self.insert(example_bibjson, ID=1)

        # lookup test example
        print self.lookup(ID=1)

    #
    # Basic API calls
    # 

    def insert(self, record=None, ID=None):
        if record == None: record = rand_bibjson()
        if ID == None:
            ID = max(self.IDs) + 1
            self.IDs.add(ID)

        # insert records into db
        self.dbCon.index(record, self.index_name, self.mapping_name, ID)

    def lookup(self, ID = 1):
        # get record with the corresponding id
        fullpath = '/' + self.index_name + '/' + self.mapping_name + '/' + str(ID)
        c =  httplib.HTTPConnection(self.host)
        c.request('GET', fullpath)
        result = c.getresponse()
        return json.loads(result.read())


    def search(self, query_string = "title:Jones"):
        fullpath = ('/' + self.index_name + 
                    '/' + self.mapping_name + 
                    '/_search?q=' + query_string)

        c =  httplib.HTTPConnection(self.host)
        c.request('GET', fullpath)
        result = c.getresponse()
        return json.loads(result.read())

    def dump_db(self):
        return self.search("*")['hits']['hits']

    
    #
    # Benchmarking tools
    # 


    def rand_instert_benchmark(self,n = 1000):
        s = STATUS("Insertion Benchmark")
        s.start()
        for i in range(n):
            self.insert(rand_bibjson())
            s.tick()
        s.stop()
        s.show()

    def rand_lookup_benchmark(self, n = 1000):
        s = STATUS("Lookup Benchmark")
        s.start()
        for i in range(n):
            self.lookup(self.rand_id())
            s.tick()
        s.stop()
        s.show()


    def rand_update_benchmark(self, n = 1000):
        key = "title"
        value = "new title"

        s = STATUS("Lookup Benchmark")
        s.start()
        for i in range(n):
            record = self.lookup(self.rand_id())
            record[key] = value
            s.tick()
        s.stop()
        s.show()

    def dump_benchmark(self):
        s = STATUS("Dump")
        s.start()
        self.dump_db()
        s.tick()
        s.stop()
        s.show()


    #
    # Helper Methods
    #
    
    def rand_id(self):
        if len(self.IDs) == 0:
            return None

        return random.sample(self.IDs, 1)[0]
    #
    # Main method
    #

    def run(self):
        print "############## random insert benchmark #############"
        self.rand_instert_benchmark(1000)
        print "############## random lookup benchmark #############"
        self.rand_lookup_benchmark(100)
        print "############## dump benchmark #############"
        self.dump_benchmark()
        
        #print "############## random lookup benchmark #############"
        #self.rand_update_benchmark(100)


from time import time

class STATUS():
    """
    Class for time mesurements.
    """
    title = ""
    timeStart = 0.0
    timeStop = 0.0
    timeLast = 0.0
    ticks  = []

    def __init__(self,title):
        self.title = title
        self.ticks = []
    
    def start(self):
        print "starting clock " + self.title
        self.timeStart = time()
        self.timeLast = self.timeStart

    def tick(self):
        timeNow = time()
        self.ticks.append(timeNow - self.timeLast)
        self.timeLast = timeNow

    def stop(self):
        print "stopping clock " + self.title
        self.timeStop = self.timeLast
   
    def show(self):
        title = self.title
        timeTotal = self.timeStop - self.timeStart
        nTicks = len(self.ticks)
        timeAverage = 1000 * timeTotal / float(nTicks)
        timeMax = 1000 * max(self.ticks)
        timeMin = 1000 * min(self.ticks)
        frequency = nTicks / float(timeTotal)
        fMax = 1.0 / (min(self.ticks) + 0.000001)
        fMin = 1.0 / (max(self.ticks) + 0.000001)

        print """\
Perfoming {title}:
* Ticks:     {nTicks} 
* Total:     {timeTotal:.3f}sec
* Frequency: {frequency:.3f} ticks/sec ({fMin:.3f} - {fMax:.3f})
* Average:   {timeAverage:.3f} msec/ticks ({timeMin:.3f} - {timeMax:.3f})
""".format(**locals())


#
# Helper
#
        
example_bibjson = {
    "title": "Open Bibliography for Science, Technology and Medicine",
    "author":[
        {"name": "Richard Jones"},
        {"name": "Mark MacGillivray"},
        {"name": "Peter Murray-Rust"},
        {"name": "Jim Pitman"},
        {"name": "Peter Sefton"},
            {"name": "Ben O'Steen"},
        {"name": "William Waites"}
        ],
    "type": "article",
    "year": "2011",
    "journal": {"name": "Journal of Cheminformatics"},
    "link": [{"url":"http://www.jcheminf.com/content/3/1/47"}],
    "identifier": [{"type":"doi","id":"10.1186/1758-2946-3-47"}]
    }


def rand_string(size=6, chars=string.ascii_uppercase + string.ascii_lowercase + string.digits):
    # http://stackoverflow.com/questions/2257441/python-random-string-generation-with-upper-case-letters-and-digits
    return ''.join(random.choice(chars) for x in range(size))

def rand_bibjson():
    return {
        "title": rand_string(40),
        "author":[
            {"name": rand_string(10)},
            {"name": rand_string(30)},
            ],
        "type": "article",
        "year": rand_string(4,string.digits),
        "journal": {"name": rand_string(40) },
        "link": [{"url": rand_string(30)}],
        "identifier": [{"type":"doi","id": rand_string(15, string.digits) }]
        }




mappings = {
    "record" : {
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
        },
    "collection" : {
        "collection" : {
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
    }


if __name__ == "__main__":
    dbb = dbBenchmark()
    dbb.run()
