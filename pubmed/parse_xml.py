import os, stat, csv, traceback, sys, time
from lxml import etree
from collections import namedtuple

from model import Article, article_field_set
from utils import get_graphs

def run(input_directory, articles_filename, citations_filename):
    writer = csv.writer(open(articles_filename, 'w'))
    citations_writer = csv.writer(open(citations_filename, 'w'))

    last_journal, i, j, started = None, 0, 0, time.time()

    for journal, filename, xml in get_graphs(input_directory):
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
                fields[datum.attrib['key']] = ' '.join((datum.text or '').split()).encode('utf-8')
            fields['id'] = article.attrib['id']
            fields['filename'] = filename
#            fields['title'] = ' '.join(fields['title'].split())
#            fields['abstract'] = ' '.join(fields['abstract'].split())
            article = Article(**fields)
            writer.writerow(article)
            del fields, article

        for citation in xml.xpath("/article-data/edge[@type='cites']"):
            try:
                count = citation.xpath("data[@key='count']")[0].text
            except IndexError:
                count = ''
            citations_writer.writerow([citation.attrib['source'], citation.attrib['target'], count])

if __name__ == '__main__':
    run('../out', '../parsed/articles-raw.csv', '../parsed/citations-raw.csv')
