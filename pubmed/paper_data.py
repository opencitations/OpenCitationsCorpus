import csv, itertools, os, shutil, zipfile
from lxml import etree

from model import Article
from urlcache import urlopen

#z = zipfile.ZipFile('examples.zip', 'w')
#for r, d, fs in os.walk('examples'):
#    for f in fs:
#        f = os.path.join(r, f)
#        z.write(f)
#z.close()

def fetch_metadata(pmid):
    response = urlopen('http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&rettype=xml&id=%s' % pmid)
    xml = etree.parse(response, parser=etree.HTMLParser())
    print xml.xpath("a[@class='ref-extlink']")



PMIDS = ['10952301', '15242645', '17510324', '9665979' , '9516219' ,
         '12167863', '11234002', '17604718', '11292640', '14652202',
         '12368864', '12364791', '11742391', '16262740', '8995086' ,
         '15699079', '15866310', '12973350', '16020726', '16020725',
         '9634230' , '9157152' , '8446170' , '17023659', '7813012' ,
         '10339583', '18431445',                                   ]

articles = itertools.starmap(Article, csv.reader(open('../parsed/articles-id-unified-sorted.csv')))

citecols, dirnames = {}, {}
for pmid in PMIDS:
    citecols[pmid] = etree.fromstring('<citation-collection pmid="%s"/>' % pmid)
    dirnames[pmid] = os.path.join('examples', pmid)
    if not os.path.exists(dirnames[pmid]):
        os.makedirs(dirnames[pmid])
        os.makedirs(os.path.join(dirnames[pmid], 'src'))
        os.makedirs(os.path.join(dirnames[pmid], 'dst'))

j = 0
for i, article in enumerate(articles):
    if i % 100000 == 0:
        print i, j

    pmid = article.pmid

    if not (pmid in PMIDS):
        continue

    if article.pmid and not article.doi:
        fetch_metadata(article.pmid)

    filename = article.filename
    filename = os.path.join(os.path.dirname(__file__), '..', 'data', filename.split('-')[0], filename)

    if article.in_oa_subset:
        print "OA", article.pmid, os.path.abspath(os.path.join(dirnames[pmid], 'original.xml'))
        shutil.copy(filename,
                    os.path.join(dirnames[pmid], 'original.xml'))
        shutil.copy(filename.replace('data', 'out', 1) + '.xml',
                    os.path.join(dirnames[pmid], 'parsed.xml'))
        continue

    j += 1


    _, citing_pmid, _, rid = article.id.split(':')

    xml = etree.parse(open(filename))

    reference = xml.xpath(".//ref[@id='%s']" % rid)

    citedoc = etree.fromstring('<citing_document filename="%s" pmid="%s"/>' % (article.filename, citing_pmid))

    for x in xml.xpath(".//xref[@rid='%s']" % rid):
        x.tail = None
        citedoc.append(x)
    for x in xml.xpath(".//ref[@id='%s']" % rid):
        x.tail = None
        citedoc.append(x)

    parsed = etree.fromstring('<parsed/>')
    for k, v in article._asdict().iteritems():
        e = etree.Element(k)
        e.text = v.decode('utf-8')
        parsed.append(e)
    citedoc.append(parsed)

    citecols[pmid].append(citedoc)

    shutil.copy2(filename, os.path.join(dirnames[pmid], 'src', article.filename))
    shutil.copy2(filename.replace('data', 'out', 1) + '.xml', os.path.join(dirnames[pmid], 'dst', article.filename))

for pmid, citecol in citecols.iteritems():
    filename = os.path.join(dirnames[pmid], 'collected.xml')

    with open(filename, 'w') as f:
        etree.ElementTree(citecol).write(f)


