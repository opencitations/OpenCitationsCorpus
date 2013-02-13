import requests, json
import Config

# a batch class for managing batches of records to send to ES, that also does the bulk loading
# this is used by the main PMC2ES class below
class Batch(object):
    def __init__(self):
        self.temp = []
        
    def add(self,doc):
        self.temp.append( doc )
        if len(self.temp) == Config.batchsize:
            self._es_bulk_load()

    def clear(self):
        if self.temp:
            self._es_bulk_load()

    def _es_bulk_load(self):
        print "sending batch of " + str(len(self.temp))
        # http://www.elasticsearch.org/guide/reference/api/bulk.html
        data = ''
        for r in self.temp:
            data += json.dumps( {'index':{'_id': r['_id']}} ) + '\n'
            data += json.dumps( r ) + '\n'
        self.temp = []
        r = requests.post(Config.es_target + '_bulk', data=data)

        return r # passing back the POST info in case it is useful

