import urllib, tarfile, simplejson, StringIO, os, traceback, time

from lxml import etree

from bibjson_util import get_json_files, write_dataset

doc_sum_dir = os.path.join(os.path.expanduser('~'), '.pubmed-doc-sum')

def run(input_filename, output_filename):
    tar_in = tarfile.open(input_filename, 'r:gz')
    tar_out = tarfile.open(output_filename, 'w:gz')

    pmids, seen, article_count = set(), set(), 0
    t = 0

    for i, (tar_info, data) in enumerate(get_json_files(tar_in)):
        data.seek(0)
        dataset = simplejson.load(data)
        data.seek(0)
        tar_out.addfile(tar_info, data)
        tar_out.members = []

        pmids |= set(r['pmid'] for r in dataset['recordList'] if r and r.get('pmid') and r['pmid'] not in seen)
        article_count += len([r for r in dataset['recordList'] if r and r.get('type') == 'Article'])

        process_pmids(tar_out, seen, pmids)

        for j in dataset['recordList']:
            if j.get('type') != 'Journal':
                continue
            #print j

        if article_count >= t:
            t = t + 10000
#            if t == 100000:
#                break
            print "%10d %10d" % (i, article_count)

    process_pmids(tar_out, seen, pmids, True)

def doc_sum_location(db, pmid):
    if db == 'pubmed':
        return os.path.join(doc_sum_dir, pmid[-4:], pmid)
    else:
        return os.path.join(doc_sum_dir, db, pmid[-4:], pmid)

def process_pmids(tar_out, seen, pmids, final=False):
    seen |= pmids
    to_convert = set()

    for pmid in list(pmids):
        filename = doc_sum_location('pubmed', pmid)
        if os.path.exists(filename):
            to_convert.add(pmid)
            pmids.remove(pmid)

    while len(pmids) >= 50 or (final and pmids):
        to_fetch = set()
        for i in range(min(len(pmids), 50)):
            to_fetch.add(pmids.pop())


        print "fetching", len(pmids), len(to_fetch)
        response = urllib.urlopen('http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&rettype=xml&id=%s' % ','.join(sorted(to_fetch)))
        try:
            xml = etree.parse(response).getroot()
        except Exception, e:
            print "Exception processing %s" % response.url
            traceback.print_exc()
            continue

        for doc_sum in xml.xpath('DocSum'):
            pmid = doc_sum.xpath('Id')[0].text
            filename = doc_sum_location('pubmed', pmid)
            if not os.path.exists(os.path.dirname(filename)):
                os.makedirs(os.path.dirname(filename))
            with open(filename, 'w') as f:
                f.write(etree.tostring(doc_sum))
            to_convert.add(pmid)

        time.sleep(min(1, max(0, process_pmids.last_request + 1 - time.time())))
        process_pmids.last_request = time.time()

    for pmid in to_convert:
        dataset = convert_doc_sum(pmid)
        tar_info = tarfile.TarInfo('pmid_api/%04d/%s.json' % (int(pmid[-4:]), pmid))
        write_dataset(tar_out, tar_info, dataset)
process_pmids.last_request = time.time()

DOC_SUM_MAP = {
    'Volume': 'volume',
    'Source': 'source',
    'Title': 'title',
    'Issue': 'issue',
}

def convert_doc_sum(pmid):
    filename = doc_sum_location('pubmed', pmid)
    with open(filename, 'r') as f:
        xml = etree.parse(f)

    items = {}
    for element in xml.xpath("Item[@Name]"):
        if element.text:
            items[element.attrib['Name']] = element.text

    record = {
        'id': 'pubmed-api:%s' % pmid,
        'type': 'Article',
    }
    records = [record]
    for k, v in DOC_SUM_MAP.iteritems():
        if items.get(k):
           record[v] = items[k]

    if 'Pages' in items:
        pages = items['Pages'].split('-')
        fpage, lpage = pages[0], pages[-1]
        lpage = fpage[:-len(lpage)] + lpage
        record['pageStart'], record['pageEnd'] = fpage, lpage
        record['pages'] = '%s--%s' % (fpage, lpage)
    if 'PubDate' in items:
        dt = items['PubDate'].split('-')
        if len(dt) > 0: record['year'] = dt[0]
        if len(dt) > 1: record['month'] = dt[1]
        if len(dt) > 2: record['day'] = dt[2]

    for i, author in enumerate(xml.xpath("Item[@Name='AuthorList']/Item[@Name='Author']")):
        id_ = 'pubmed-api:%s:author:%d' % (pmid, i)
        records.append({
            'id': id_,
            'type': 'Person',
            'name': author.text,
        })
        if 'author' not in record:
            record['author'] = []
        record['author'].append({'ref': '@%s' % id_})

    journal = {}
    if 'FullJournalName' in items:
        journal['name'] = items['FullJournalName']
    if 'ISSN' in items:
        journal['issn'] = items['ISSN']
    if 'ESSN' in items:
        journal['eissn'] = items['ESSN']
    if 'Source' in items:
        journal['x-nlm-ta'] = items['Source']
    if journal:
        journal['id'] = 'pubmed-api:%s:journal' % pmid
        journal['type'] = 'Journal'
        record['journal'] = {'ref': '@pubmed-api:%s:journal' % pmid}
        records.append(journal)

    for identifier in xml.xpath("Item[@Name='ArticleIds']/Item"):
        scheme, value = identifier.attrib['Name'], identifier.text
        if scheme in ('pii', 'doi'):
            record[scheme] = value
        elif scheme == 'pubmed':
            record['pmid'] = value
        elif scheme == 'pmc':
            record['pmc'] = value.replace('PMC', '')
        elif scheme in ('pmcid', 'mid'):
            pass
        else:
            print "Unknown identifier scheme: %s (%r)" % (scheme, value)

    dataset = {
        'dataset': {},
        'recordList': records,
    }
    return dataset

#def fetch_journal_data():
#    for i in range

if __name__ == '__main__':
#    import cProfile, pstats
#    cProfile.run("run('../parsed/articles-raw.bibjson.tar.gz', '../parsed/articles-augmented.bibjson.tar.gz')", 'tmp')
#    stats = pstats.Stats('tmp')
#    stats.sort_stats('cumulative')
#    stats.print_stats()

    run('../parsed/articles-raw.bibjson.tar.gz', '../parsed/articles-augmented.bibjson.tar.gz')


