import os
from lxml import etree

def indexOf(dummy, *args):
    print dummy, args

ns = etree.FunctionNamespace(None)
ns['index-of'] = indexOf


transform = etree.XSLT(etree.parse(open('article-data.xsl')))

for journal in os.listdir(os.path.join('..', 'data')):
    for filename in os.listdir(os.path.join('..', 'data', journal)):
        filename = os.path.join('..', 'data', journal, filename)
        try:
            transform(etree.parse(open(filename)))
        except Exception, e:
            print e.error_log
        break
    break


