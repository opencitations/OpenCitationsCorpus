import os, stat, csv, traceback, sys, time
from lxml import etree
from collections import namedtuple

from model import Article, article_field_set
from utils import get_graphs

writer = csv.writer(open('../parsed/articles.csv', 'w'))
last_journal, i, j, started = None, 0, 0, time.time()

for journal, filename, xml in get_graphs():
    if last_journal != journal:
        last_journal, i, duration = journal, i + 1, time.time() - started
        if last_journal:
            print "%4d %4d %6.2f %6.4f %s" % (i, j, duration, (duration / j) if j else 0, last_journal)
        j, started = 0, time.time()
    j += 1

    for article in xml.xpath("/article-data/node[@type='article']"):
        fields = dict((n, '') for n in article_field_set)
        for datum in article.xpath('data'):
            if datum.attrib['key'] not in article_field_set:
                continue
            fields[datum.attrib['key']] = (datum.text or '').encode('utf-8')
        fields['id'] = article.attrib['id']
        fields['filename'] = filename
        fields['title'] = ' '.join(fields['title'].split())
        fields['abstract'] = ' '.join(fields['abstract'].split())
        article = Article(**fields)
        writer.writerow(article)
        del fields, article

