import os, urllib, hashlib

base_dir = os.path.join(os.path.expanduser('~'), '.urlcache')

def urlopen(url):
    filename = hashlib.sha1(url).hexdigest()
    filename = os.path.join(base_dir, filename[:3], filename[3:6], filename)

    if os.path.exists(filename):
        return open(filename, 'r')
    elif not os.path.exists(os.path.dirname(filename)):
        os.makedirs(os.path.dirname(filename))

    urllib.urlretrieve(url, filename)

    return open(filename, 'r')

