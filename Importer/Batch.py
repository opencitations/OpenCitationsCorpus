import requests, json
import Config
from Matcher import Matcher
import logging
import datetime
import os

if not os.path.exists('./log/'):
    os.mkdir('./log/')

now = datetime.datetime.now()
logging.basicConfig(filename=now.strftime('./log/batch-%Y-%m-%d.log'),level=logging.DEBUG)

# a batch class for managing batches of records to send to ES, that also does the bulk loading
class Batch(object):
    def __init__(self):
        self.temp = []
        
    def add(self,doc):
        self.temp.append( doc )
        if len(self.temp) == Config.elasticsearch['batchsize']:
            self._es_bulk_load()

    def clear(self):
        if self.temp:
            self._es_bulk_load()

    def _es_bulk_load(self):
        print "sending batch of " + str(len(self.temp))
        # http://www.elasticsearch.org/guide/reference/api/bulk.html
        data = ''
        for r in self.temp:
            print(r)
            print(json.dumps( r ))
            data += json.dumps( {'index':{'_id': r['_id']}} ) + '\n'
            data += json.dumps( r ) + '\n'
        self.temp = []
        logging.debug(data)
        r = requests.post(Config.elasticsearch['uri_records'] + '_bulk', data=data)

        # if matching is enabled, then try to match whatever was in the batch to the rest of the index content
        if Config.importer['load']['pubmedcentral']['do_bulk_match']:
            print "matching"
            m = Matcher()
            m.citesandcitedby(self.temp)

        return r # passing back the POST info in case it is useful

