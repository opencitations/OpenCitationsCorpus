import os, stat, traceback, sys, time
from datetime import datetime
from lxml import etree

def get_graphs(input_directory):
    #directories = sorted(os.listdir('out'), key=lambda x:max([0]+[os.stat(os.path.join('out', x, y))[stat.ST_MTIME] for y in os.listdir(os.path.join('out', x))]), reverse=True)
    directories = os.listdir(input_directory)
    directories.sort()
    for directory in directories:
        if not os.path.isdir(os.path.join(input_directory, directory)):
            continue
        for filename in os.listdir(os.path.join(input_directory, directory)):
            filename = os.path.join(input_directory, directory, filename)
            if os.stat(filename).st_size > 10e6:
                print "Skipping %r" % filename
                continue
            #if datetime.fromtimestamp(os.stat(filename).st_mtime) < datetime(2011, 03, 02, 11, 0, 0):
            #    break
            if filename.endswith('.xml'):
                try:
                    with open(filename) as f:
                        xml = etree.parse(f)
                    yield directory, os.path.splitext(os.path.basename(filename))[0], xml
                except Exception:
                    print "Error in %s" % filename
                    traceback.print_exc(file=sys.stderr)
                    pass

