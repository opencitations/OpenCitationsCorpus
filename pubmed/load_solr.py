import solr, itertools, csv, functools

from model import Article

reader = csv.reader(open('../parsed/articles.csv', 'r'))

def group(it, size):
    it = iter(it)
    def subit(it, first, size):
        yield first
        for i in xrange(size):
            yield it.next()
    while True:
        yield subit(it, it.next(), size-1)

s = solr.SolrConnection('http://localhost:8983/solr')

for g in group(reader, 10000):
    print "Loading"
    g = (Article(*(f.decode('utf-8') for f in article))._asdict() for article in g)
    s.add_many(g)

