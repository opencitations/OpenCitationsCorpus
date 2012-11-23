import itertools, csv, re
from collections import namedtuple
import solr

from model import Article

Disease = namedtuple('Disease', ['name', 'terms', 'filename'])
DISEASES = []

for line in itertools.islice(csv.reader(open('orr.csv')), 4, None):
    filename='orr/disease-%s.csv' % re.sub(r'\W+', '-', line[0].lower().strip())
    disease = Disease(name=line[0].strip(), terms=line[1].split(', '), filename=filename)
    DISEASES.append(disease)

#s = solr.SolrConnection('http://localhost:8983/solr')
#
#def article(x):
#    def f(a):
#        x[0] += 1
#        a.pop('score')
#        a['keywords'] = tuple(sorted(a['keywords']))
#        a['author'] = tuple(sorted(a['author']))
#        return Article(**a)
#    return f

if __name__ == '__main__':

    articles = itertools.starmap(Article, csv.reader(open('../parsed/articles-tidy-old.csv')))
    oa_subset = csv.writer(open('orr/oa_subset.csv', 'w'))
    identifiers = csv.writer(open('orr/identifiers.csv', 'w'))

    writers = []
    for disease in DISEASES:
        writers.append((
            csv.writer(disease.filename, 'w'),
            re.compile(r'(\b%s\b)' % r'\b|\b'.join(map(re.escape, disease.terms)), re.I),
        ))
    writers = tuple(writers)

    for article in articles:
        for writer, regex in writers:
            if any(map(regex.search, (article.title, article.keywords, article.abstract))):
                writer.writerow(article)
        if article.in_oa_subset:
            oa_subset.writerow([article.id])
        identifiers.writerow([article.id, article.pmid, article.pmc, article.doi, article.uri])

