import os, stat, traceback, sys, time
from datetime import datetime
from lxml import etree

def get_graphs(input_directory, filter=lambda directory,filename:True):
    """
    It looks like this script searches through all xml 
    files in subdirectories of input_directory
    and yields the parsed xml tree as etree object.
    """
    #directories = sorted(os.listdir('out'), key=lambda x:max([0]+[os.stat(os.path.join('out', x, y))[stat.ST_MTIME] for y in os.listdir(os.path.join('out', x))]), reverse=True)

    print "get_graph: running on", input_directory

    directories = os.listdir(input_directory)
    directories.sort()
    for directory in directories:
        print "get_graph: processing directory", directory

        #if directory != 'PLoS_Negl_Trop_Dis': continue
        if not os.path.isdir(os.path.join(input_directory, directory)):
            # skip if not a directory
            continue


        for filename in os.listdir(os.path.join(input_directory, directory)):
            # print "get_graph: processing file", filename

            if not filter(directory, filename):
                print "get_graph: Filtered out", filename
                continue

            filename = os.path.join(input_directory, directory, filename)
            if os.stat(filename).st_size > 10e6:
                print "get_graph: Skipping %r -- too big" % filename
                continue

            #if datetime.fromtimestamp(os.stat(filename).st_mtime) < datetime(2011, 03, 02, 11, 0, 0):
            #    break


            if filename.endswith('.xml'):
                print "get_graph: processing xml-file", filename
                try:
                    with open(filename) as f:
                        xml = etree.parse(f)
                    yield directory, os.path.splitext(os.path.basename(filename))[0], xml
                except Exception:
                    print "Error in %s" % filename
                    traceback.print_exc(file=sys.stderr)
                    pass
            else:
                # print "get_graph: skipped file", filename, "- not an .xml"
                pass

