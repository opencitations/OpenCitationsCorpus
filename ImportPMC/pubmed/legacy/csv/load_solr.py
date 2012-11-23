import solr, itertools, csv, functools

from model import Article

def run(filename):

    reader = csv.reader(open(filename, 'r'))

    def group(it, size):
        it = iter(it)
        def subit(it, first, size):
            yield first
            for i in xrange(size):
                yield it.next()
        while True:
            yield subit(it, it.next(), size-1)

    s = solr.SolrConnection('http://localhost:8983/solr')

    def quorum(articles):
        articles = list(articles[1])
        return articles[0]

    def get_article(article):
        article = Article(*(f.decode('utf-8') for f in article))._asdict()
        article['keywords'] = article['keywords'].split(u', ')
        return article

    reader = itertools.imap(quorum, itertools.groupby(reader, key=lambda x:x[0]))

    for i, g in enumerate(group(reader, 10000)):
        print "Loading", i
        s.add_many(itertools.imap(get_article, g))

    s.commit()

