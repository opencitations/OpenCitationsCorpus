import os, stat, csv, traceback, sys, time
from lxml import etree
from collections import namedtuple

def get_graphs():
    #directories = sorted(os.listdir('out'), key=lambda x:max([0]+[os.stat(os.path.join('out', x, y))[stat.ST_MTIME] for y in os.listdir(os.path.join('out', x))]), reverse=True)
    directories = os.listdir('out')
    for directory in directories:
        for filename in os.listdir(os.path.join('out', directory)):
            filename = os.path.join('out', directory, filename)
            if filename.endswith('.xml'):
                try:
                    yield directory, etree.parse(open(filename))
                except Exception:
                    print "Error in %s" % filename
                    traceback.print_exc(file=sys.stderr)
                    pass

field_names = ("id xml_container ctype journal doi pmid pmc isbn " +
               "full_citation year month day title author source " +
               "license " +
               "publisher issue volume edition fpage lpage").split()
field_name_set = set(field_names)
Article = namedtuple('Article', field_names)


writer = csv.writer(open('parsed/articles.csv', 'w'))
last_journal, i, j, started = None, 0, 0, time.time()

for journal, xml in get_graphs():
    if last_journal != journal:
        last_journal, i, duration = journal, i + 1, time.time() - started
        if last_journal:
            print "%4d %4d %6.2f %6.4f %s" % (i, j, duration, (duration / j) if j else 0, last_journal)
        j, started = 0, time.time()
    j += 1

    for article in xml.xpath("/article-data/node[@type='article']"):
        fields = dict((n, '') for n in field_names)
        for datum in article.xpath('data'):
            if datum.attrib['key'] not in field_name_set:
                continue
            fields[datum.attrib['key']] = (datum.text or '').encode('utf-8')
        fields['id'] = article.attrib['id']
        article = Article(**fields)
        writer.writerow(article)

