from __future__ import division
import os, stat, traceback, sys, csv
import itertools
import pprint
import resource
from collections import defaultdict
from math import log

from model import Article
from recluster import recluster

IDENTIFIERS = ('pmid', 'doi', 'pmc', 'uri', 'patent_number', 'isbn')

def run(input_filename, output_filename):
    articles = defaultdict(set)

    without_identifiers = set()

    reader = csv.reader(open(input_filename, 'r'))

    try:
        biggest = 0

        for i, article in enumerate(reader):
            article = Article(*article)
            identifiers = [(k,v) for k,v in article._asdict().items() if k in IDENTIFIERS and v]
            data = None # dict(identifiers)
            if not identifiers:
                without_identifiers.add(article.id)
                continue
            articles[identifiers[0]].add(article.id)
            for identifier in identifiers[1:]:
                if articles[identifiers[0]] is not articles[identifier]:
                    articles[identifiers[0]] |= articles[identifier]
                    articles[identifier] = articles[identifiers[0]]
                    if len(articles[identifier]) > biggest:
                        biggest = len(articles[identifier])

            if i % 10000 == 0:
                print "%7d" % i, resource.getrusage(resource.RUSAGE_SELF)[2], biggest
                if resource.getrusage(resource.RUSAGE_SELF)[2] > 1e7:
                    print "Using too much memory"
                    raise Exception
    except Exception, e:
        print e

    articles = dict((id(l), l) for l in articles.values()).values()

    groups = {}
    for i, article_list in enumerate(articles):
        for article_id in article_list:
            groups[article_id] = i

    for article in without_identifiers:
        i += 1
        groups[article] = i


    reader = csv.reader(open(input_filename, 'r'))
    writer = csv.writer(open(output_filename, 'w'))

    try:
        for i, article in enumerate(reader):
            article = Article(*article)._asdict()
            article['group'] = '%09i' % groups[article['id']]
            article = Article(**article)
            writer.writerow(article)

            if i % 10000 == 0:
                print "%7d" % i, resource.getrusage(resource.RUSAGE_SELF)[2:5]
    except:
        raise
        pass

if __name__ == '__main__':
    run('../parsed/articles-raw.csv', '../parsed/articles-id-unified.csv')
