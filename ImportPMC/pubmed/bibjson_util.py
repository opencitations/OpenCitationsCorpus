import simplejson, StringIO
import base64, pickle
import sys
import time

def get_records(tar, with_index=False, types=('Article',)):
    for tar_info in tar:
        if tar_info.name.endswith('.json'):
            json = tar.extractfile(tar_info)
            json = StringIO.StringIO(json.read())
            json = simplejson.loads(json.getvalue())
            if with_index:
                index = {}
                for record in json['recordList']:
                    if record:
                        index[record['id']] = record
            else:
                index = None
            for record in json['recordList']:
                if record and record['type'] in types:
                    yield index, record

def get_datasets(tar, types=('Article', 'Journal')):
    i, j, last_j = 0, 0, 0
    start_time = batch_start_time = time.time()
    for tar_info in tar:
        if tar_info.name.endswith('.json'):
            i += 1
            json = tar.extractfile(tar_info)
            json = simplejson.load(json)
            if types is None or any(r['type'] in types for r in json['recordList']):
                j += 1
                yield tar_info, json
            if i % 10000 == 0:
                sys.stderr.write("%10d %10d %8.2f %8.2f\n" % (i, j, j/(time.time() - start_time), (j-last_j)/(time.time() - batch_start_time)))
                batch_start_time, last_j = time.time(), j
                tar.members = []

def get_json_files(tar):
    for tar_info in tar:
        if tar_info.name.endswith('.json'):
            json = tar.extractfile(tar_info)
            yield tar_info, StringIO.StringIO(json.read())

def write_dataset(tar, tar_info, json):
    data = StringIO.StringIO()
#    data.write(simplejson.dumps(json, indent='  '))
    data.write(simplejson.dumps(json, indent=2))
    data.seek(0)
    tar_info.size = data.len
    tar.addfile(tar_info, data)
    tar.members = []

def serialize(obj):
    return base64.b64encode(pickle.dumps(obj))
def deserialize(s):
    return pickle.loads(base64.b64decode(s))
