import csv, itertools, sys
from collections import defaultdict
from model import Article
from open_research import DISEASES

all_oa_subset = set(l[0] for l in csv.reader(open('orr/oa_subset.csv')) if l)
identifiers = dict((l[0], l[1:]) for l in csv.reader(open('orr/identifiers.csv')) if l)
out = csv.writer(sys.stdout)

# Load all citations
citations = defaultdict(set)
rev_citations = defaultdict(set)
for c in csv.reader(open('../parsed/citations-tidy-old.csv')):
    citations[c[0]].add(c[1])
    rev_citations[c[1]].add(c[0])

for disease in DISEASES:

    articles = itertools.starmap(Article, csv.reader(open(disease.filename)))

    disease_citation_distribution = defaultdict(int)
    disease_oa_citation_distribution = defaultdict(int)

    disease_articles = set()
    disease_oa_subset = set()
    disease_oa_subset_cited = set()
    article_citation_counts = {}

    for article in articles:
        article_citation_count = len(rev_citations[article.id])
        disease_citation_distribution[article_citation_count] += 1
        article_citation_counts[article.id] = article_citation_count
        disease_articles.add(article.id)

        if not article.in_oa_subset:
            continue

        if rev_citations[article.id]:
            disease_oa_subset_cited.add(article.id)

        disease_oa_subset.add(article.id)
        disease_oa_citation_distribution[article_citation_count] += 1

    article_citation_counts = sorted(article_citation_counts.items(), key=lambda x:x[1], reverse=True)[:20]


    if False:
        print (' %s ' % disease.name).center(80, '=')
        print "Disease-relevant papers", len(disease_articles)
        print "Disease-relevant papers in OA subset", len(disease_oa_subset)
        print "Number cited in OA", len(disease_oa_subset_cited)
        print "Number of disease-relevant papers cited by other disease-relevant papers in OA subset", sum(v for k,v in disease_oa_citation_distribution.items() if k)
        print [(identifiers[k][0], v) for k,v in article_citation_counts]
    else:
        out.writerow([
            disease.name,
            ', '.join(disease.terms),
            len(disease_articles),
            len(disease_oa_subset),
            len(disease_oa_subset_cited),
        ] + list(itertools.chain(*[(identifiers[k][0], v) for k,v in article_citation_counts])))







# print '='*8, filename, '='*8
# print "Number of disease-relevant papers overall", sum(topic_citation_distribution.values())
# print "Number of disease-relevant papers in OA subset", len(oa_subset)
# print "Number of disease-relevant papers cited by other disease-relevant papers in OA subset", sum(v for k,v in citation_distribution.items() if k)
# #print "Number of references to any paper from disease-relevant papers in OA subset", reference_count
# #print "Number of unique cited papers cited from disease-relevant papers in OA subset", len(seen)
# print "Number cited in OA", len(all_oa_subset & seen)
# print "OA citation distribution", sorted(citation_distribution.items())
# #print "Citation distribution", sorted(all_citation_distribution.items())
# print "Related citation distribution", sorted(topic_citation_distribution.items())

