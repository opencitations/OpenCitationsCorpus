import os, stat, traceback, sys
from lxml import etree

def get_graphs():
    #directories = sorted(os.listdir('out'), key=lambda x:max([0]+[os.stat(os.path.join('out', x, y))[stat.ST_MTIME] for y in os.listdir(os.path.join('out', x))]), reverse=True)
    directories = os.listdir('../out')
    for directory in directories:
        for filename in os.listdir(os.path.join('..', 'out', directory)):
            filename = os.path.join('..', 'out', directory, filename)
            if os.stat(filename).st_size > 10e6:
                print "Skipping %r" % filename
                continue
            if filename.endswith('.xml'):
                try:
                    with open(filename) as f:
                        xml = etree.parse(f)
                    yield directory, os.path.splitext(os.path.basename(filename))[0], xml
                except Exception:
                    print "Error in %s" % filename
                    traceback.print_exc(file=sys.stderr)
                    pass

