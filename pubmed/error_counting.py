import tarfile
import pprint
from collections import defaultdict

from bibjson_util import get_datasets
from bibjson_rdf import majority_vote, normalize_field
from compare import compare

tar = tarfile.open('../parsed-recent/articles-unified.bibjson.tar.gz', 'r:gz')

mappings = defaultdict(dict)

def format_article(article, mappings, records):
    authors = ', '.join(normalize_field(a, mappings, records).get('name', '-').replace(',', '').replace('.', '') for a in article.get('author', ()))
    return '%30s  %10s  %80s  %100s' % (
        article.get('doi', '')[:30].ljust(30),
        article.get('pmid', '')[:10].ljust(10),
        article.get('title', '')[:80].ljust(80),
        authors[:100].ljust(100),
    )



for tar_info, dataset in get_datasets(tar, ('Article',)):
    records = dataset['recordList']
    articles = [r for r in records if r.get('type') == 'Article']
    canonical, fields = majority_vote(records, ('Article',), mappings)

    records = dict((r['id'], r) for r in records)

    for record in records:
        v = compare(canonical, record, records)
        print v

    print '='*80
    print format_article(canonical, mappings, records)
    print '-'*80
    for article in articles:
        print format_article(article, mappings, records)
    print '='*80
    print

