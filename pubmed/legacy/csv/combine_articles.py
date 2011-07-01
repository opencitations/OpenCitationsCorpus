from model import Article, article_fields
import itertools, csv
from collections import defaultdict
from functools import partial

class Combiner(object):
    def __init__(self):
        for field_name in article_fields:
            if not hasattr(self, field_name):
                setattr(self, field_name, partial(self.default, name=field_name))

    def title(self, articles):
        titles = defaultdict(int)
        for article in articles:
            titles[article.title] += 1

        _, title = max((count*len(title)**2, title) for title, count in titles.items())
        return title

#    def id(self, articles):
#        for article in articles:
#            if article.id.count(':') == 1:
#                return article.id
#        else:
#            return self.default(articles, 'id')

    def default(self, articles, name):
        fields = (' '.join(getattr(article, name).split()) for article in articles)
        fields = filter(bool, fields)
        counts = defaultdict(int)
        for field in fields:
            counts[field] += 1
        if not counts:
            return ''
        field, _ = max(counts.iteritems(), key=lambda x:(x[1], x[0]))
        return field

    def combine_articles(self, articles):
#        for article in articles:
#            if article.id.count(':') == 1:
#                return article
        article = {}
        for field_name in article_fields:
            article[field_name] = getattr(self, field_name)(articles)
        return Article(**article)

#    def filename(self, articles):
#        for article in articles:
#            if article.id.count(':') == 1:
#                return article.filename
#        else:
#            return self.default(articles, 'filename')



def run(input_filename, output_filename, mapping_output_filename):
    reader = csv.reader(open(input_filename))
    writer = csv.writer(open(output_filename, 'w'))
    mapping_writer = csv.writer(open(mapping_output_filename, 'w'))
    reader = (Article(*(f.decode('utf-8') for f in a)) for a in reader)

    combiner = Combiner()

    for group_id, articles in itertools.groupby(reader, lambda a:a.group):
        articles = list(articles)
#        print '='*80
#        for article in articles:
#            print "%8s %8s %40s %120s" % (article.pmc, article.pmid, article.doi[:40].ljust(40), article.title[:120].ljust(120))
        article = combiner.combine_articles(articles)
#        print '-'*80
#        print "%8s %8s %40s %120s" % (article.pmc, article.pmid, article.doi[:40].ljust(40), article.title[:120].ljust(120))
        writer.writerow([f.encode('utf-8') for f in article])

        for a in articles:
            mapping_writer.writerow([a.id, article.id])


def combine_articles(group_id, articles):
    if len(articles) == 1:
        return articles[0]

    keywords = set()
    for article in articles:
        keywords |= set(kw.strip() for kw in article.keywords.split(','))
    new_article['keywords'] = ','.join(keywords)

    titles = defaultdict(int)
    for article in articles:
        titles[article.title] += 1

    _, title = max((count*len(title)**2, title) for title, count in titles.items())
    new_article['title'] = title

    for name in 'pmc pmid doi'.split():
        identifiers = defaultdict(int)
        for article in articles:
            if getattr(article, name):
                identifiers[getattr(article, name)] += 1
        if identifiers:
            _, identifier = max(map(swap, identifiers.items()))
            new_article[name] = identifier


    return Article(**new_article)

if __name__ == '__main__':
    run('../parsed/articles-id-unified-sorted.csv', '../parsed/articles-tidy.csv', '../parsed/id-mapping.csv')
