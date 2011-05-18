import csv, urlparse, itertools, threading, os, urllib, time
from functools import partial
import Queue

from lxml import etree

from model import Article, article_field_set
from urlcache import urlopen

def sanitize_uri(uri):
    uri = urlparse.urlparse(uri)
    uri = uri._replace(scheme=(uri.scheme or 'http'),
                       path=(uri.path or '/'),
                       netloc=(uri.netloc.lower()))
    return urlparse.urlunparse(uri)

PREFIXES = {
    'us': ('US', 'U.S.', 'United States',),
    'wipo': ('WO', 'Patent WO',),
    'fr': ('French patent application'),
    'euro': ('EP',),
    'de': ('German Pat.'),
}

def sanitize_patent_number(value):
    for domain, prefixes in PREFIXES.iteritems():
        if any(value.startswith(p) for p in prefixes):
            break
    else:
        if not value[0].isdigit():
            raise ValueError("Unexpected prefix: %r" % value)
        domain = 'us'

    if False and domain == 'wipo':
        value = value.rsplit('/', 1)
        value = map(partial(filter, lambda c:c.isdigit()), value)
        if len(value[0]) == 2:
            value[0] = ('19' if value[0] > 11 else '20') + value[0]
        value = value[-1] #'/'.join(value)
    else:
        value = ''.join(filter(lambda c:c.isdigit(), value.rsplit('/', 1)[-1]))
        value = int(value)

    return '%s:%s' % (domain, value)


def retrieve_doc_sums(root_dir, pmids):

    response = urllib.urlopen('http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&rettype=xml&id=%s' % ','.join(sorted(pmids)))
    xml = etree.parse(response).getroot()

    for doc_sum in xml.xpath('DocSum'):
        yield doc_sum.xpath('Id')[0].text, doc_sum

    print "Fetched", len(pmids)

    time.sleep(1)

def doc_sum_location(root_dir, pmid):
    return os.path.join(root_dir, pmid[-4:], pmid)

def doc_sum_to_article(xml):
    def f(xml, name):
        value = xml.xpath("Item[@Name='%s']" % name)
        return (value[0].text or '') if value else ''
    months = {'Jan': '1', 'Feb': '2', 'Mar': '3', 'Apr': '4', 'May': '5', 'Jun': '6',
              'Jul': '7', 'Aug': '8', 'Sep': '9', 'Oct': '10', 'Nov': '11', 'Dec': '12',
              'Win': '', 'Spr': '', 'Sum': '', 'Fal': '', 'Aut': ''}

    pages = f(xml, 'Pages').split('-')
    pubdate = f(xml, 'PubDate').split()

    data = dict((k, '') for k in article_field_set)
    data.update({
        'id': 'pmid:%s:api' % xml.xpath('Id')[0].text,
        'provenance': 'pubmed_api',
        'author': ', '.join(a.text for a in xml.xpath("Item[@Name='AuthorList']/Item[@Name='Author']")),
        'volume': f(xml, 'Volume'),
        'journal': f(xml, 'Source'),
        'title': f(xml, 'Title'),
        'issue': f(xml, 'Issue'),
        'fpage': pages[0],
        'lpage': pages[0][:-len(pages[-1])] + pages[-1],
        'year': pubdate[0] if len(pubdate) >= 1 else '',
        'month': months.get(pubdate[1][:3], '') if len(pubdate) >= 2 else '',
        'day': pubdate[2] if len(pubdate) == 3 else '',
    })

    for identifier in xml.xpath("Item[@Name='ArticleIds']/Item"):
        scheme, value = identifier.attrib['Name'], identifier.text
        if scheme == 'pubmed':
            data['pmid'] = value
        elif scheme == 'pmc':
            data['pmc'] = value.replace('PMC', '')
        elif scheme == 'pii':
            data['pii'] = value
        elif scheme == 'doi':
            data['doi'] = value
        elif scheme == 'mid':
            data['nihmsid'] = value
        elif scheme in ('pmcid',):
            pass
        else:
            print "Unknown identifier scheme: %s (%r)" % (scheme, value)

    data = dict((k, v.encode('utf-8')) for k, v in data.iteritems())

    return Article(**data)


def run(input_filename, output_filename):
    output_queue = Queue.Queue(1024)
    pubmed_retrieve_queue = Queue.Queue(1024)
    pubmed_parse_queue = Queue.Queue(1024)
    bail = threading.Event()

    input_thread = threading.Thread(target=process_input, args=[input_filename, pubmed_retrieve_queue, output_queue, bail], name="input")
    pubmed_retrieve_thread = threading.Thread(target=process_pubmed_retrieve, args=[pubmed_retrieve_queue, pubmed_parse_queue, bail], name="pubmed_retrieve")
    pubmed_parse_thread = threading.Thread(target=process_pubmed_parse, args=[pubmed_parse_queue, output_queue, bail], name="pubmed_parse")
    output_thread = threading.Thread(target=process_output, args=[output_filename, output_queue, bail], name="output")

    print "Starting threads"
    for thread in (output_thread, pubmed_retrieve_thread, pubmed_parse_thread, input_thread):
        print "Starting", thread
        thread.start()

    print "Running"

    try:
        for thread in (pubmed_retrieve_thread, pubmed_parse_thread, input_thread):
            thread.join()
            print "Joined", thread
    finally:
        output_queue.put(None)
        output_thread.join()

def process_input(input_filename, pubmed_retrieve_queue, output_queue, bail):
    try:
        reader = csv.reader(open(input_filename))
        last_source = None

        for i, article in enumerate(itertools.starmap(Article, reader)):
            if bail.is_set():
                break

            if i % 1000 == 0:
                print " IN %10i" % i

            article = sanitize(article)

            source = article.filename.split('-')[0]
            if source != last_source:
                last_source = source
                print " IN %10i %s" % (i, source)

            output_queue.put(article)

            if article.provenance == 'pmc_oa_reference' and article.pmid:
                pubmed_retrieve_queue.put(article.pmid)
    except:
        bail.set()
        raise

    finally:
        pubmed_retrieve_queue.put(None)

def process_pubmed_retrieve(pubmed_retrieve_queue, pubmed_parse_queue, bail):
    try:
        root_dir = os.path.join(os.path.expanduser('~'), '.pubmed-doc-sum')

        if not os.path.exists(root_dir):
            os.makedirs(root_dir)

        seen_pmids, queue, i, duplicates = set(), set(), 0, 0
        while not bail.is_set():
            pmid = pubmed_retrieve_queue.get()
            if pmid is not None:
                if pmid in seen_pmids:
                    duplicates += 1
                    continue
                seen_pmids.add(pmid)

                if i % 1000 == 0:
                    print "RET %10i %10i" % (i, duplicates)
                i += 1


                filename = doc_sum_location(root_dir, pmid)
                if os.path.exists(filename):
                    doc_sum = etree.parse(open(filename))
                    pubmed_parse_queue.put(doc_sum)
                else:
                    queue.add(pmid)

            if pmid is None or len(queue) >= 50:
                for pmid_, doc_sum in retrieve_doc_sums(root_dir, queue):
                    filename = doc_sum_location(root_dir, pmid_)
                    if not os.path.exists(os.path.dirname(filename)):
                        os.makedirs(os.path.dirname(filename))
                    with open(filename, 'w') as f:
                        f.write(etree.tostring(doc_sum))
                    pubmed_parse_queue.put(doc_sum)
                queue.clear()

            if pmid is None:
                break

    except:
        bail.set()
        raise

    finally:
        pubmed_parse_queue.put(None)

def process_pubmed_parse(pubmed_parse_queue, output_queue, bail):
    try:
        while not bail.is_set():
            doc_sum = pubmed_parse_queue.get()
            if doc_sum is None:
                break

            output_queue.put(doc_sum_to_article(doc_sum))
    except:
        bail.set()
        raise

def process_output(output_filename, output_queue, bail):
    try:
        writer = csv.writer(open(output_filename, 'w'))

        i = 0
        while not bail.is_set():
            article = output_queue.get()
            if article is None:
                break

            if i % 1000 == 0:
                print "OUT %10i" % i
            i += 1

            writer.writerow(article)
    except:
        bail.set()
        raise


def sanitize(article):
    if article.uri:
        try:
            article = article._replace(uri=sanitize_uri(article.uri))
        except Exception, e:
            pass
            #print article.uri, repr(e)
    if article.patent_number:
        try:
            print "%40s %40s" % (article.patent_number, sanitize_patent_number(article.patent_number))
            article = article._replace(patent_number=sanitize_patent_number(article.patent_number))
        except Exception, e:
            pass
    return article

if __name__ == '__main__':
    run('../parsed/articles-raw.csv', '../parsed/articles-sanitized.csv')
