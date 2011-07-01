import os, urllib, urllib2, hashlib, simplejson, time

base_dir = os.path.join(os.path.expanduser('~'), '.urlcache')

class CachedResource(object):
    def __init__(self, url, data=None, delay=0):
        request_hash = 'POST' if data else 'GET'
        request_hash += url
        if data:
            data = urllib.urlencode(sorted(data.iteritems()))
            request_hash += '?' + data
        filename = hashlib.sha1(request_hash).hexdigest()
        self.filename = os.path.join(base_dir, filename[:3], filename[3:6], filename)
        self.meta_filename = self.filename + '.meta'

        if not os.path.exists(self.filename):
            if delay:
                time.sleep(delay)
            if not os.path.exists(os.path.dirname(self.filename)):
                os.makedirs(os.path.dirname(self.filename))
            meta = {}
            response = urllib2.urlopen(url, data)
            meta.update({
                'requested_url': url,
                'url': response.url,
                'code': response.code,
                'headers': dict(response.headers),
            })
            try:
                with open(self.filename, 'w') as f:
                    while True:
                        chunk = response.read(1024)
                        if not chunk:
                            break
                        f.write(chunk)
            except:
                os.unlink(self.filename)
                raise
            with open(self.meta_filename, 'w') as f:
                simplejson.dump(meta, f)
        else:
            response = open(self.filename)
            with open(self.meta_filename) as f:
                meta = simplejson.load(f)

        self.response = response
        for k in meta:
            setattr(self, k, meta[k])

    def __getattr__(self, name):
        return getattr(self.response, name)

    def getcode(self):
        return self.code
    def geturl(self):
        return self.url


def urlopen(url, data=None, delay=0):
    return CachedResource(url, data, delay)

    filename = hashlib.sha1(url).hexdigest()
    filename = os.path.join(base_dir, filename[:3], filename[3:6], filename)

    if os.path.exists(filename):
        return open(filename, 'r')
    elif not os.path.exists(os.path.dirname(filename)):
        os.makedirs(os.path.dirname(filename))

    urllib.urlretrieve(url, filename)

    return open(filename, 'r')

