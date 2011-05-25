import simplejson, tarfile, StringIO, time
from lxml import etree

from utils import get_graphs
from model import article_field_set

class Data(dict):
    def __init__(self, xml):
        self._id, self._type = xml.attrib['id'], xml.attrib['type']
        for datum in xml.xpath('data'):
            self[datum.attrib['key']] = datum.text

    def __getattr__(self, name):
        return self.get(name) or None


ARTICLE_FIELDS = """title year month day volume edition author editor cites
                    doi pmid isbn pmc uri publisher""".split()
ARTICLE_MAP = {'description': 'abstract', 'pageStart': 'fpage', 'pageEnd': 'lpage', 'citation': 'full_citation'}

def article_record(xml, node, data):
    data.cites, data.author, data.editor, data.translator, data.retracts = [], [], [], [], []
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
        else:
            print "Unknown type: %r %r" % (ptype, contrib_type)
            print etree.tostring(edge)
            continue
        l.append({
            'ref': '@%s' % edge.attrib['target'],
        })

    record = {
        'id': data._id,
        'type': 'Article',
    }

    for article_field in ARTICLE_FIELDS:
        if getattr(data, article_field):
            record[article_field] = getattr(data, article_field)
    for a, b in ARTICLE_MAP.iteritems():
        if getattr(data, b):
            record[a] = getattr(data, b)
    if data.fpage and data.lpage:
        record['pages'] = '--'.join([data.fpage, data.lpage])

    return record

def person_record(xml, node, data):
    record = {
        'id': data._id,
        'type': 'Person',
        'name': '%s, %s' % (data.surname, data.get('given-names')),
    }
    return record

def organisation_record(xml, node, data):
    record = {
        'id': data._id,
        'type': 'Organization',
        'address': data.address,
    }

def run(input_directory, articles_filename):
    tar = tarfile.open(articles_filename, 'w:gz')

    last_journal, i, j, started = None, 0, 0, time.time()

    for journal, filename, xml in get_graphs(input_directory):
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

        for node in xml.xpath("/article-data/node"):
            data = Data(node)

            if data._type == 'article':
                record_list.append(article_record(xml, node, data))
            elif data._type == 'person':
                record_list.append(person_record(xml, node, data))
            elif data._type == 'affiliation':
                record_list.append(organisation_record(xml, node, data))
            else:
                print data._type


        tar_info = tarfile.TarInfo('pmc_open_access/%s/%s' % (journal, filename.replace('.nxml', '.json')))
        data = StringIO.StringIO()
        simplejson.dump(dataset, data)
        tar_info.size = data.len
        data.seek(0)
        tar.addfile(tar_info, data)


    tar.close()

if __name__ == '__main__':
    run('../out', '../parsed/articles-raw.bibjson.tar.gz')


