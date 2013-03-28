import requests, json
import Config

# This matcher class tries to find matches between records in the index
# Given a record it can look for other records in the index that appear to match the citations in the given record
# And it can look for other records in the index that appear to cite the given record

# When matches are found, the relevant records are updated in the index

# To use this, instantiate a Matcher then call matchall() to try to run it on everything in the configured index
# Or call citesandcitedby with a list of record IDs or full record objects to run on

# It is also possible to call cites({...}) or citedby({...}) directly, providing one full record object as the parameter

class Matcher(object):

    def __init__(self):
        self.target = Config.es_target
        self.qry = {
            "query": {
                "bool": {
                    "must": []
                }
            }
        }

        
    # try to match every record in the whole index
    def matchall(self, bsize=1000, limit=0, _from=0):
        total = requests.get(self.target + '_search').json().get('hits',{}).get('total',0)
        if limit != 0 and limit < total: total = limit
        if limit != 0 and limit < bsize: bsize = limit
        while _from < total:
            tgt = self.target + '_search?size=' + str(bsize) + '&from=' + str(_from)
            rlist = [i.get('_source',{}) for i in requests.get(tgt).json().get('hits',{}).get('hits',[])] 
            self.citesandcitedby(rlist)
            _from += bsize

    
    # try to match every record in the provided list with any other record in the whole index by both citing and being cited
    def citesandcitedby(self, rlist=[]):
        count = 1
        for r in rlist:
            print count
            count += 1 
            if not isinstance(r,dict):
                r = requests.get(self.target + r['_id']).json()
            self.cites(r)
            self.citedby(r)


    # find out which records the given record cites, add them to the _reference list, and save it
    def cites(self,record):
        update = False
        for cite in record.get('citation',[]):
            # the citation should form a rudimentary record object
            cite['_id'] = record['_id'] # pass the parent record ID with the cite so not to match self
            for _id, rec in self._findthis(cite, isacite=True).iteritems():
                update = True
                record = self._update_references(record, rec)
        if update:
            print "saving cites"
            requests.post(self.target + record['_id'], data=json.dumps(record))


    # finds the records that cite the provided record, update to show the _reference the provided record, and save them
    def citedby(self, record):
        # for records that do appear to cite this one
        for _id, rec in self._findthis(record).iteritems():
            rec = self._update_references(rec, record)
            print "saving citedby"
            requests.post(self.target + rec['_id'], data=json.dumps(rec))

        
    def _findthis(self, record, isacite=False):
        # add records that cite this one to an object where each record is keyed by its ID
        matchobj = {}

        # see if any other record cites this one by title
        # TODO: should probably make this a fuzzy lowercase match or something like that
        if 'title' in record:
            if isacite:
                self.qry["query"]["bool"]["must"] = [{"term":{"title.exact": record["title"]}}]
            else:
                self.qry["query"]["bool"]["must"] = [{"term":{"citation.title.exact": record["title"]}}]
            self.qry["query"]["bool"]["must_not"] = [{"term":{"_id.exact": record["_id"]}}]
            #print self.qry
            results = self._get_results(self.qry)
            for res in results:
                res['spotted'] = matchobj.get(res['_id'],{}).get('spotted',0) + 1
                res['lastmatch'] = record['title']
                matchobj[res['_id']] = res
            
        # see if any other record cites this one by ID
        for ident in record.get('identifier',[]):
            if isacite:
                self.qry["query"]["bool"]["must"] = [{"term":{"identifier.canonical.exact": ident["canonical"]}}]
            else:
                self.qry["query"]["bool"]["must"] = [{"term":{"citation.identifier.canonical.exact": ident["canonical"]}}]
            self.qry["query"]["bool"]["must_not"] = [{"term":{"_id.exact": record["_id"]}}]
            #print self.qry
            results = self._get_results(self.qry)
            for res in results:
                res['spotted'] = matchobj.get(res['_id'],{}).get('spotted',0) + 1
                res['lastmatch'] = ident['canonical']
                matchobj[res['_id']] = res
                
         # add other matching functions in here if necessary
        return matchobj


    def _get_results(self,q):
        return [i.get('_source',{}) for i in requests.post(self.target + '_search', data=json.dumps(q)).json().get('hits',{}).get('hits',[])]


    # if the _reference list of inthisrec does not cite tothisrec then add it
    def _update_references(self, inthisrec, tothisrec):
        if '_reference' not in inthisrec: inthisrec['_reference'] = []
        #refobj = tothisrec['_id']
        refobj = {
            "_id": tothisrec["_id"],
            "spotted": tothisrec.get("spotted",inthisrec.get("spotted","")),
            "lastmatch": tothisrec.get("lastmatch",inthisrec.get("lastmatch",""))
        }
        #if tothisrec['_id'] not in inthisrec['_reference']: inthisrec['_reference'].append(refobj)
        if tothisrec['_id'] not in [i['_id'] for i in inthisrec['_reference']]: inthisrec['_reference'].append(refobj)
        if "spotted" in inthisrec: del inthisrec["spotted"]
        if "lastmatch" in inthisrec: del inthisrec["lastmatch"]
        return inthisrec
    

        
# add options to this to run bulk or not
if __name__ == "__main__":
    from datetime import datetime
    started = datetime.now()
    print started
    matcher = Matcher()
    matcher.matchall(limit=100)
    ended = datetime.now()
    print ended
    print ended - started
        

