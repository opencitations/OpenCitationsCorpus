import sys
from bibjson_util import *
from collections import defaultdict
import tarfile
import pprint

tar = tarfile.open('../parsed-recent/articles-raw.bibjson.tar.gz', 'r:gz')

oa_count, ref_count, unique_count, augmented_count = 0, 0, 0, 0

years = defaultdict(int)
years_cited = defaultdict(lambda:defaultdict(int))
years_cited_two = defaultdict(int)

identifier_prevalence = defaultdict(int)
identifier_group_prevalence = defaultdict(int)
identifier_types = set('pmid pmc doi'.split())

for i, (tar_info, dataset) in enumerate(get_datasets(tar, None)):
    break
    if not dataset['recordList']:
        continue
    oa_count += 1
    ref_count += len([r for r in dataset['recordList'] if r.get('x-source-type')=='pmc_oa_reference' and r['type']=='Article'])

    k = defaultdict(list)
    for r in dataset['recordList']:
        if r['type'] == 'Article':
            k[r['x-source-type']].append(r)
        if r['type'] == 'Article' and r.get('x-source-type') == 'pmc_oa_reference':
            identifier_prevalence[frozenset(t for t in identifier_types if r.get(t))] += 1

    try:
        year = k['pmc_oa'][0]['year']
        assert 1979 < int(year) < 2011
    except Exception:
        year = None

    years[year] += 1
    for r in k['pmc_oa_reference']:
        try:
            cited_year = r.get('year')[:4]
            assert 1979 < int(cited_year) < 2011
        except:
            cited_year = None
        years_cited[year][cited_year] += 1
        years_cited_two[cited_year] += 1


    if i % 10000 == 0:
        print i, oa_count, ref_count
        pprint.pprint(dict(identifier_prevalence))
        #pprint.pprint(dict(years))
        #pprint.pprint(dict(years_cited_two))
#        pprint.pprint(dict((k, dict(v)) for k,v in years_cited.iteritems()))

tar.close()


print "OA Count:", oa_count
print "Reference Count:", ref_count
print "Total article count", oa_count + ref_count

tar = tarfile.open('../parsed-recent/articles-augmented.bibjson.tar.gz', 'r:gz')

type_counts = defaultdict(int)
type_heirarchy = 'Report PersonalCommunication Book ConferenceProceedings ComputerProgram Thesis WebSite WebPage Patent JournalArticle Expression'.split()

for i, (tar_info, dataset) in enumerate(get_datasets(tar, ('Article',))):
    break
    augmented_count += len([r for r in dataset['recordList'] if r['id'].startswith('pubmed-api:') and r['type']=='Article'])
    if i % 100000 == 0:
        print i, augmented_count

print "Augmented count", augmented_count

tar.close()
tar = tarfile.open('../parsed-recent/articles-unified.bibjson.tar.gz', 'r:gz')

years = defaultdict(lambda: [0,0])

citation_counts = defaultdict(int)

highly_cited = []

for i, (tar_info, dataset) in enumerate(get_datasets(tar, ('Article',))):
    unique_count += 1

    type_counts[frozenset(r.get('x-fabio-type') for r in dataset['recordList'] if r.get('x-fabio-type'))] += 1

    articles = list(r for r in dataset['recordList'] if r.get('type') == 'Article')
    source_types = set(a.get('x-source-type') for a in articles)

    citation_count = len([r for r in articles if r.get('x-source-type')=='pmc_oa_reference'])
    citation_counts[citation_count] += 1

    if citation_count >= 287:
        ids = {}
        for scheme in 'doi pmid pmc'.split():
            ids[scheme] = set(a.get(scheme) for a in articles)
        highly_cited.append((ids, citation_count))

    identifier_group_prevalence[frozenset(t for t in identifier_types for r in articles if r.get(t))] += 1

    ys = defaultdict(int)
    for article in articles:
        try:
            year = article['year'][:4]
            ys[year] += 1
        except Exception:
            year = None

    try:
        year = sorted(ys, key=lambda y:-ys[y])[0]
        if 1950 <= int(year) <= 1979:
            year = "EARL"
        else:
            assert 1979 < int(year) < 2011
    except Exception:
        year = None

    if 'pmc_oa' in source_types:
        years[year][0] += 1
    if 'pmc_oa_reference' in source_types:
        years[year][1] += 1

    if i % 10000 == 0:
        print i, oa_count, ref_count
        pprint.pprint(dict(identifier_group_prevalence))
        #print '='*80
        #for y in sorted(years):
        #    print "%4s,%s" % (y, ','.join(map(str, years[y])))
        #print '-'*80
        #for y in sorted(citation_counts):
        #    print "%d,%d" % (y, citation_counts[y])
        #print '='*80
        #pprint.pprint(highly_cited)
        #pprint.pprint(dict(years))

    if i % 100000 == 0:
        print i, unique_count
        d = defaultdict(int)
        for k in type_counts:
            for t in type_heirarchy:
                if t in k:
                    d[t] += type_counts[k]
                    break
            else:
                print "E", k
        pprint.pprint(dict(d))

d = defaultdict(int)
for k in type_counts:
    for t in type_heirarchy:
        if t in k:
            d[t] += type_counts[k]
            break
    else:
        print "E", k

highly_cited.sort(key=lambda x:x[1])

print "Type groups:"
pprint.pprint(dict(type_counts))
print "OA Count:", oa_count
print "Reference Count:", ref_count
print "Total article count", oa_count + ref_count
print "Augmented count", augmented_count
print "Unique count", unique_count
print "Processed types:"
pprint.pprint(dict(d))
print "ID prevalence"
pprint.pprint(dict(identifier_prevalence))
print "Grouped ID prevalence"
pprint.pprint(dict(identifier_group_prevalence))
print "Highly cited"
pprint.pprint(highly_cited)
