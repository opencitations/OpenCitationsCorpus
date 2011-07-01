from __future__ import division
import os, stat, traceback, sys
import itertools
import pprint
from collections import defaultdict
from math import log

import networkx
from graphml import read_graphml

graph = networkx.DiGraph()

def get_filenames():
    for root, dirs, files in os.walk('out/'):
        for filename in files:
            filename = os.path.join(root, filename)
            if filename.endswith('.xml'):
                yield filename

def get_graphs():
    directories = sorted(os.listdir('out'), key=lambda x:max([0]+[os.stat(os.path.join('out', x, y))[stat.ST_MTIME] for y in os.listdir(os.path.join('out', x))]), reverse=True)
    for directory in directories:
        for filename in os.listdir(os.path.join('out', directory)):
            filename = os.path.join('out', directory, filename)
            if filename.endswith('.xml'):
                try:
                    yield directory, read_graphml(filename)
                except Exception:
                    traceback.print_exc(file=sys.stderr)
                    pass


IDENTIFIERS = ('pmid', 'doi')
articles = defaultdict(list)

without_identifiers = 0

try:
    i = 0
    for journal, graph in get_graphs():

        for node, data in graph.nodes(data=True):
            identifiers = [(k,v) for k,v in data.items() if k in IDENTIFIERS and v]
            data = None # dict(identifiers)
            if not identifiers:
                without_identifiers += 1
                continue
            articles[identifiers[0]].append((node, data))
            for identifier in identifiers[1:]:
                if articles[identifiers[0]] is not articles[identifier]:
                    articles[identifiers[0]] += articles[identifier]
                    articles[identifier] = articles[identifiers[0]]

        i += 1
        if (i % 500) == 0:
            counts, unique_articles = defaultdict(int, {0: without_identifiers}), {}
            ids = defaultdict(list)
            for identifier, article in articles.iteritems():
                unique_articles[id(article)] = article
                ids[id(article)].append(identifier)


#            print '#'*80
            for id_, article in unique_articles.iteritems():
                counts[len(article)] += 1
#                if len(article) > 100:
#                    print len(article), set(tuple(a[1].items()) for a in article)

            counts = sorted(counts.items())
            print "-"*80
            total = sum(a[1] for a in counts)
            for a,b in counts:
                if b > 3:
                    lv = log(b)/log(2)
                    print "%8d | %6.2f%% | %8d | %s%s" % (a, b/total*100, b, "=" * int(lv), '-' if lv%1 > 0.5 else '')

except KeyboardInterrupt:
    pass



counts, unique_articles = defaultdict(int, {0: without_identifiers}), {}
for identifier, article in articles.iteritems():
    unique_articles[id(article)] = article

for article in unique_articles.itervalues():
    counts[len(article)] += 1

print counts



#pprint.pprint(identifiers)
