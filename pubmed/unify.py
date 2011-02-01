from __future__ import division
import os, stat, traceback, sys, csv
import itertools
import pprint
from collections import defaultdict
from math import log

from model import Article
from recluster import recluster


IDENTIFIERS = ('pmid', 'doi')
articles = defaultdict(list)

without_identifiers = 0

reader = csv.reader(open('../parsed/articles.csv', 'r'))
writer = csv.writer(open('../parsed/clustered.csv', 'w'))

try:
    for i, article in enumerate(reader):
        article = Article(*article)
        identifiers = [(k,v) for k,v in article._asdict().items() if k in IDENTIFIERS and v]
        data = None # dict(identifiers)
        if not identifiers:
            without_identifiers += 1
            continue
        articles[identifiers[0]].append(article)
        for identifier in identifiers[1:]:
            if articles[identifiers[0]] is not articles[identifier]:
                articles[identifiers[0]] += articles[identifier]
                articles[identifier] = articles[identifiers[0]]

        if i % 10000 == 0:
            print "%7d" % i
except:
    pass


i = 0
for group in articles.itervalues():
    groups = recluster(group)
    for group in groups:
        for article in group:
            article = article._asdict()
            article['group'] = i
            article = Article(**article)
            writer.writerow(article)
        i += 1

    if i % 10000 == 0:
        print "%7d" % i
