import datetime
import simplejson
import tarfile
import StringIO
import time
import ftplib
import os
import csv
import urlparse

from lxml import etree

from utils import get_graphs

class Data(dict):
    def __init__(self, xml):
        self._id, self._type = xml.attrib.get('id'), xml.attrib.get('type')
        for datum in xml.xpath('data'):
            self[datum.attrib['key']] = datum.text

    def __getattr__(self, name):
        return self.get(name) or None


ARTICLE_FIELDS = """title year month day volume edition author editor cites
                    doi pmid isbn pmc publisher journal""".split()
ARTICLE_MAP = {
    'abstract': 'abstract',
    'pageStart': 'fpage',
    'pageEnd': 'lpage',
    'citation': 'full_citation',
    'x-in-text-reference-pointer-count': 'in_text_reference_pointer_count',
    'x-reference-count': 'reference_count',
    'x-fabio-type': 'fabio_type',
    'x-source-type': 'provenance',
    'url': 'uri',
}

ORGANIZATION_MAP = {
    'x-nlm-publisher-id': 'publisher-id',
    'address': 'address',
    'name': 'name',
}

JOURNAL_MAP = {
    'nlm_ta': 'x-nlm-ta',
    'title': 'title',
    'issn': 'issn',
    'eissn': 'eissn',
}

def article_record(xml, node, data):
    record = {
        'id': data._id,
        'type': 'Article',
    }

    data.cites, data.author, data.editor, data.translator, data.retracts = [], [], [], [], []
    data.journal = None
    for edge in xml.xpath("/article-data/edge[@source='%s']" % data._id):
        ptype = edge.attrib['type']
        try:
            contrib_type = edge.xpath("data[@key='contrib-type']")[0].text
        except IndexError:
            contrib_type = None
        if ptype == 'cites':
            l = data.cites
        elif ptype == 'retracts':
            l = data.retracts
        elif ptype == 'contributor' and contrib_type in ('allauthors', 'author'):
            l = data.author
        elif ptype == 'contributor' and contrib_type == 'editor':
            l = data.editor
        elif ptype == 'contributor' and contrib_type == 'translator':
            l = data.translator
        elif ptype== 'journal':
            data.journal = {'ref': '@%s' % edge.attrib['target']}
            continue
        else:
            print "Unknown type: %r %r" % (ptype, contrib_type)
            print etree.tostring(edge)
            continue
        l.append({
            'ref': '@%s' % edge.attrib['target'],
        })


    for article_field in ARTICLE_FIELDS:
        value = getattr(data, article_field)
        if value:
            record[article_field] = value.strip() if isinstance(value, basestring) else value
    for a, b in ARTICLE_MAP.iteritems():
        if getattr(data, b):
            record[a] = getattr(data, b).strip()
    if data.fpage and data.lpage:
        record['pages'] = '--'.join([data.fpage, data.lpage])

    return record

def journal_record(xml, node, data):
    journal = {
        'id': data._id,
        'type': 'Journal',
        'x-nlm-ta': getattr(data, 'nlm_ta'),
    }

    for edge in xml.xpath("/article-data/edge[@source='%s']" % data._id):
        if edge.attrib['type'] == 'publisher':
            journal['publisher'] = {'ref': '@%s' % edge.attrib['target']}
    for a, b in JOURNAL_MAP.iteritems():
        if getattr(data, b):
            journal[a] = data[b]

    return journal


def person_record(xml, node, data):
    record = {
        'id': data._id,
        'type': 'Person',
        'x-name-style': (data.get('name-style') or 'western').strip(),
    }
    if data.get('name') and not (data.get('surname') and data.get('given-names')):
        record['name'] = data['name'].strip()
    if data.get('surname'):
        record['name'] = record['x-surname'] = data['surname'].strip()
    if data.get('given-names'):
        record['x-given-names'] = data['given-names'].strip()
        if 'name' in record:
            record['name'] += ", " + record['x-given-names']

    for edge in xml.xpath("/article-data/edge[@source='%s']" % data._id):
        if edge.attrib['type'] == 'affiliation':
            record['affiliated'] = {'ref': '@%s' % edge.attrib['target']}
    return record

def organisation_record(xml, node, data):
    record = {
        'id': data._id,
        'type': 'Organization',
    }
    for a, b in ORGANIZATION_MAP.iteritems():
        if getattr(data, b):
            record[a] = data[b]
    return record

def get_source_url_mapping():
    cached_filename = os.path.join(os.path.expanduser('~'), '.pubmed', 'file_list.csv')
    if not os.path.exists(os.path.dirname(cached_filename)):
        os.makedirs(os.path.dirname(cached_filename))
    ftp = ftplib.FTP('ftp.ncbi.nlm.nih.gov')
    ftp.connect()
    ftp.login('anonymous', 'anonymous')
    ftp.cwd('pub/pmc')
    result = ftp.sendcmd('MDTM file_list.csv').split()
    if result[0] != '213' or len(result) != 2:
        raise ValueError("NIH FTP server responded unexpectedly")
    mt = result[1]
    mt = mt[:4], mt[4:6], mt[6:8], mt[8:10], mt[10:12], mt[12:14]
    mtime = time.mktime(tuple(map(int, mt))+(0,0,0))
    if not os.path.exists(cached_filename) or \
       os.stat(cached_filename).st_mtime > mtime:
        print "Fetching new copy of file list from NIH FTP server"
        with open(cached_filename, 'w') as f:
            ftp.retrbinary('RETR file_list.csv', f.write)
        os.utime(cached_filename, (time.time(), mtime))
    ftp.quit()

    url_mapping = {}
    with open(cached_filename, 'r') as f:
        reader = csv.reader(f)
        reader.next() # Skip the first line
        for row in reader:
            path, pmc_id = row[0], row[2][3:]
            url_mapping[pmc_id] = urlparse.urljoin('ftp://ftp.ncbi.nlm.nih.gov/pub/pmc/', path)

    return url_mapping

def seen_before(seen):
    def seen_filter(directory, filename):
        return filename not in seen
    return seen_filter

def reis(directory, filename):
    return filename == 'PLoS_Negl_Trop_Dis-2-4-2292260.nxml.xml'

def subset(directory, filename):
    return directory in SUBSET_DIRECTORIES
SUBSET_DIRECTORIES = set([
    'BMC_Med_Res_Methodol', 'PLoS_Comput_Biol', 'PLoS_Med', 'PLoS_Negl_Trop_Dis',
    'BMC_Int_Health_Hum_Rights', 'BMC_Bioinformatics', 'J_Biomed_Semantics',
    'BMC_Infect_Dis', 'Nucleic_Acids_Res',
])

print SUBSET_DIRECTORIES - set(os.listdir('../data'))

def run(input_directory, articles_filename):
    seen = set()
    parse_lock_filename = os.path.join(os.path.expanduser('~'), '.pubmed', 'parse.lock')
    if os.path.exists(articles_filename) and os.path.exists(parse_lock_filename):
        os.rename(articles_filename, articles_filename+'.old')

    tar = tarfile.open(articles_filename, 'w:gz')

    if os.path.exists(articles_filename+'.old'):
        print "Loading previous progress"
        try:
            old_tar = tarfile.open(articles_filename+'.old', 'r:gz')
        except:
            print "Failed to load previous progress"
        else:
            for tar_info in old_tar:
                if tar_info.name.endswith('.json'):
                    seen.add(tar_info.name.replace('.json', '.nxml').rsplit('/', 1)[-1])
                data = old_tar.extractfile(tar_info)
                tar.addfile(tar_info, data)
            old_tar.close()
            os.unlink(articles_filename+'.old')
            print "Done loading previous progress, found %d articles" % len(seen)

    # Touch the lock file to say we've started.
    with open(parse_lock_filename, 'w') as f: pass

    last_journal, i, j, started = None, 0, 0, time.time()
    url_mapping = get_source_url_mapping()

    for journal, filename, xml in get_graphs(input_directory, filter=subset): #seen_before(seen)):
        if last_journal != journal:
            last_journal, i, duration = journal, i + 1, time.time() - started
            if last_journal:
                print "%4d %4d %6.2f %6.4f %s" % (i, j, duration, (duration / j) if j else 0, last_journal)
            j, started = 0, time.time()
        j += 1

        record_list = []
        dataset = {
            'recordList' : record_list,
        }

        pmc = xml.xpath("/article-data/node[1]/data[@key='pmc']")
        source_url = None
        if not len(pmc):
            print "No PMC found for article"
        elif pmc[0].text in url_mapping:
            source_url = url_mapping[pmc[0].text]
        else:
            print "Couldn't find source URL for PMC%s (%s)" % (pmc[0].text, filename)

        for node in xml.xpath("/article-data/node"):
            data = Data(node)

            if not data._id:
                print "Missing id:", filename

            if data._type == 'article':
                record = article_record(xml, node, data)
            elif data._type == 'person':
                record = person_record(xml, node, data)
            elif data._type == 'journal':
                record = journal_record(xml, node, data)
            elif data._type in ('organisation', 'organization'): # I can't spell
                record = organisation_record(xml, node, data)
            else:
                print data._type, filename
                print etree.tostring(node)
                continue

            if source_url:
                record['x-source-url'] = source_url
            record_list.append(record)


        tar_info = tarfile.TarInfo('pmc_open_access/%s/%s' % (journal, filename.replace('.nxml', '.json')))
        data = StringIO.StringIO()
        simplejson.dump(dataset, data, indent='  ')
        tar_info.size = data.len
        data.seek(0)
        tar.addfile(tar_info, data)

    if os.path.exists(parse_lock_filename):
        os.unlink(parse_lock_filename)

if __name__ == '__main__':
    run('../out', '../parsed/articles-raw.bibjson.tar.gz')


