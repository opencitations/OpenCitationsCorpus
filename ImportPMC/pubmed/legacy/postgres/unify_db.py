from __future__ import division
from solr import SolrConnection
from pprint import pprint
import itertools, re, operator, os
import csv
from collections import namedtuple, defaultdict
import psycopg2
from Levenshtein import distance as levenshtein_distance

def levenshtein(a, b):
        d = levenshtein_distance(a, b) / max(len(a), len(b))
        return (1 - d)

def compare_authors(a, b):
    a_names, b_names = a.decode('utf-8').replace(u'.', u'').split(u', '), b.decode('utf-8').replace(u'.', u'').split(u', ')

    cs = []

    for (i, a_name), b_name in zip(enumerate(a_names), b_names):
        a_name, b_name = a_name.split(' '), b_name.split(' ')
        if len(a_name) > len(b_name):
            a_name, b_name = b_name, a_name

        a_name = sorted(itertools.chain(*[(p if p.isupper() else [p]) for p in a_name if p]), key=lambda x:(-len(x), x))
        b_name = sorted(itertools.chain(*[(p if p.isupper() else [p]) for p in b_name if p]), key=lambda x:(-len(x), x))

        for (j, a_part), b_part in itertools.product(enumerate(a_name), b_name):
            if len(a_part) == 1 or len(b_part) == 1:
                # One is an initial
                cs.append(((i, j), (1, 1 if a_part[0] == b_part[0] else 0)))
            else:
                cs.append(((i, j), (1, levenshtein(a_part.lower(), b_part.lower()))))
            #print a_part, b_part, cs[-1]

    cs.sort(key=lambda x:-x[1][1])
    seen = set()
    ds = []
    for c, d in cs:
        if c in seen:
            continue
        seen.add(c)
        ds.append(d)

    #print "DS", ds, a, b, sum(c*d for c,d in ds) / sum(c for c,d in ds)

    try:
        return 0.7, sum(a*b for a,b in ds) / sum(a for a,b in ds)
    except ZeroDivisionError:
        return 0, 0



INTEGER_RE = re.compile('^\d+')
def compare_integer(a, b, weight=1):
    a = INTEGER_RE.match(a)
    b = INTEGER_RE.match(b)
    if a and b:
        a, b = a.group(0), b.group(0)
        # Use Levenshtein as typos appear to occur relatively often
        return (weight, levenshtein(a, b))
    else:
        return (0, 0)

def compare(a, b):
    cs = []
    if a.doi and b.doi:
        cs.append((0.4, 1 if a.doi == b.doi else 0))
    if a.pmid and b.pmid:
        cs.append((0.4, 1 if a.pmid == b.pmid else 0))
    if a.volume and b.volume:
        cs.append(compare_integer(a.volume, b.volume, weight=0.4))
    if a.issue and b.issue:
        cs.append(compare_integer(a.issue, b.issue, weight=0.4))
    if a.source and b.source:
        cs.append((0.4, levenshtein(a.source.decode('utf-8').replace('.', '').lower(), b.source.decode('utf-8').replace('.', '').lower())))
    if a.title and b.title:
        cs.append((1, levenshtein(a.title.decode('utf-8').lower(), b.title.decode('utf-8').lower())))
    if a.author and b.author:
        cs.append(compare_authors(a.author, b.author))
    if a.year and b.year:
        try:
            if int(a.year) < 1800 or int(b.year) < 1800:
                raise ValueError
            cs.append((0.5, 2** -(abs(int(a.year)-int(b.year)) / 3)))
        except ValueError:
            pass
    try:
        return sum(a for a,b in cs) / sum(a*b for a,b in cs) - 1
    except ZeroDivisionError:
        return float('inf')

class DistanceCache(defaultdict):
    def __missing__(self, key):
        if key[0] > key[1]:
            return self[(key[1], key[0])]
        distance = compare(*key)
        self[key] = distance
        return distance

def recluster(cluster):
    cluster = set(cluster)
    distances = DistanceCache()

    new_clusters = []
    while cluster:
        current_distances = dict((article, float('inf')) for article in cluster)
        current_distances[cluster.pop()] = 0
        new_cluster = set()
        while current_distances:
            distance, selected = min((b,a) for (a,b) in current_distances.iteritems())
            if distance > 0.4:
                break
            new_cluster.add(selected)
            del current_distances[selected]
            current_distances.update((
                a, min(current_distances[a],
                       distance+distances[(a, selected)])
                ) for a in current_distances)

        new_clusters.append(new_cluster)
        cluster -= new_cluster
    return new_clusters

Article = namedtuple('Article',
                     ['id', 'container', 'ctype', 'journal', 'doi', 'pmid',
                      'pmc', 'isbn', 'full_citation', 'year', 'month', 'day',
                      'title', 'author', 'source', 'publisher', 'issue',
                      'volume', 'edition'])

if __name__ == '__main__':

    conn = psycopg2.connect(user='pubmed', password='pubmed', database='pubmed')
    c = conn.cursor()
    solr = SolrConnection("http://129.67.25.213:8983/solr")


    seen = set()

    if True:
        i, j = 0, 0
        while True:
            articles = []
            c.execute("SELECT * FROM article LIMIT 10000 OFFSET %d" % j)
            for row in c.fetchall():
                if row[0] in seen:
                    continue
                seen.add(row[0])
                if row[13]:
                    author = [a.split(' ') for a in row[13].decode('utf-8').split(', ')]
                    author = [' '.join(itertools.chain(*[(p if p.isupper() else [p]) for p in a if p])) for a in author]
                    author = ', '.join(author)
                    row = row[:13] + (author,) + row[14:]
#                print row[13]

                articles.append(Article(*(cell.decode('utf-8') if isinstance(cell, str) else cell for cell in row)))
                i += 1
            solr.add_many(a._asdict() for a in articles)
            j += 10000
            if j % 1e5 == 0:
                print "Loaded: ", i
            if c.rowcount == 0:
                break
    #    writer = csv.writer(open('articles.csv', 'wb'))
    #    writer.writerows(articles)
    else:
        reader = csv.reader(open('articles.csv', 'rb'))
        for i, row in enumerate(reader):
            articles.append(Article(*(cell.decode('utf-8') for cell in row)))
            if i % 1e5 == 0:
                print "Loaded: ", i

    del seen

    print "Article records: ", len(articles)
    #old_articles, articles, seen = articles, [], set()
    #while old_articles:
    #    article = old_articles.pop()
    #    if article.id in seen:
    #        continue
    #    seen.add(article.id)
    #    articles.append(article)
    #print "Unique articles: ", len(articles)
    #del old_articles, seen

    identifiers = defaultdict(set)

    for article in articles:
        article_identifiers = []
        for name in ('pmid', 'doi'):
            identifier = name, getattr(article, name)
            if identifier[1]:
                article_identifiers.append(identifier)
                identifiers[identifier].add(article)
        for identifier in article_identifiers[1:]:
            if identifiers[identifier] is not identifiers[article_identifiers[0]]:
                identifiers[article_identifiers[0]] |= identifiers[identifier]
                identifiers[identifier] = identifiers[article_identifiers[0]]

    clusters = set(itertools.imap(tuple, identifiers.itervalues()))

    print "Clusters: ", len(clusters)
    print "Biggest:  ", max(len(cluster) for cluster in clusters)
    print "Total:    ", sum(len(cluster) for cluster in clusters)

    sizes = defaultdict(int)
    for cluster in clusters:
        sizes[len(cluster)] += 1
    sizes = sizes.items()
    sizes.sort()

    print sizes

    def map_recluster(clusters):
        while clusters:
            for cluster in itertools.imap(tuple, recluster(clusters.pop())):
                if cluster:
                    yield cluster

    for i, cluster in enumerate(map_recluster(clusters)):
        for article in cluster:
            if article.title:
                break
        else:
            continue
        id_ = article.id.split(':')
        path = os.path.join("titles", id_[1][:4], id_[1][4:], id_[2] if len(id_)==3 else '_')
        if not os.path.exists(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))
        with open(path, 'w') as f:
            f.write(article.title)

        if i % 1e5 == 0:
            print "Written %d" % i


#    for cluster in clusters:
#        if len(cluster) == 1:
#            continue
#        reclustered = recluster(cluster)
##        print map(len, reclustered)
#        for article in set(':'.join(a.id.split(':')[:2])+':' for a in cluster):
#            matching = filter(bool, (set(a for a in c if a.id.startswith(article)) for c in reclustered))
#            cluster_count = len(matching)
#            if cluster_count < 2:
#                continue
#            chained_matching = reduce(operator.or_, matching, set())
#            pairs = set((a.doi, a.pmid) for a in chained_matching if a.doi and a.pmid)
#
#            if any(len([m for m in matching if any((a.doi, a.pmid) == pair for a in m)]) > 1 for pair in pairs):
#                pprint(matching)
#                print
#        if len(reclustered) > 1:
#            pprint(reclustered)

