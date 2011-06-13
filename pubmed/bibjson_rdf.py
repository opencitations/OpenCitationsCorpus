# coding: utf-8
from collections import defaultdict
import pprint
import random
import string
import sys
import tarfile
from urlparse import urljoin

from rdflib import Literal, URIRef, Namespace

BASE = 'http://opencitationdata.org/'


from bibjson_util import get_datasets

NS = {
    'biro': 'http://purl.org/spar/biro/',
    'c4o': 'http://purl.org/spar/c4o/',
    'cito': 'http://purl.org/spar/cito/',
    'collections': 'http://swan.mindinformatics.org/ontologies/1.2/collections/',
    'dcterms': 'http://purl.org/dc/terms/',
    'fabio': 'http://purl.org/spar/fabio/',
    'foaf': 'http://xmlns.com/foaf/0.1/',
    'frbr': 'http://purl.org/vocab/frbr/core#',
    'prism': 'http://prismstandard.org/namespaces/basic/2.0/',
    'pro': 'http://purl.org/spar/pro/',
    'pso': 'http://purl.org/spar/pso/',
    'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
    'rdfs': 'http://www.w3.org/2000/01/rdf-schema#',
    'skos': 'http://www.w3.org/2004/02/skos/core#',
    'xsd': 'http://www.w3.org/2001/XMLSchema#',
}
NS = type('Namespaces', (dict,), {'__getattr__': lambda self,key: self[key]})((k, Namespace(v)) for k,v in NS.items())

BIRO = NS.biro
CITO = NS.cito
COLLECTIONS = NS.collections
DCTERMS = NS.dcterms
FABIO = NS.fabio
FRBR = NS.frbr
PRISM = NS.prism
RDF = NS.rdf
XSD = NS.xsd

def normalize_field(value, mappings, records):
    if isinstance(value, dict) and 'ref' in value:
        ref = value['ref'][1:]
        if ref in mappings['id']:
            value = mappings['id'][ref]
        elif ref in records:
            value = records[ref]
    if isinstance(value, dict):
        value = tuple(sorted((k, normalize_field(v, mappings, records)) for k,v in value.iteritems()))
    if isinstance(value, list):
        value = tuple(normalize_field(v, mappings, records) for v in value)
    return value

def majority_vote(records, types, mappings):
    records = dict((r['id'], r) for r in records)

    fields = defaultdict(lambda:defaultdict(int))
    for record in records.itervalues():
        if record['type'] not in types:
            continue
        for field, value in record.iteritems():
            value = normalize_field(value, mappings, records)
            fields[field][value] += 1
    ret = {}
    for field, values in fields.items():
        values = fields[field] = sorted(values.iteritems(), key=lambda x:-x[1])
        ret[field] = values[0][0]
    return ret, fields

def sluggify(s):
    r = []
    for c in s:
        if c in STRIP_CHARACTERS:
            continue
        if c in BAD_CHARACTERS:
            if r and r[-1] != '-':
                r.append('-')
        else:
            r.append(c.lower())
    return ''.join(r).rstrip('-')
STRIP_CHARACTERS = u'‘’“”'
BAD_CHARACTERS = string.punctuation + string.whitespace


def process_journals(input_filename, writer, mappings):
    tar = tarfile.open(input_filename, 'r:gz')
    for tar_info, journal in get_datasets(tar, types=('Journal',)):
        process_journal(journal['recordList'], writer, mappings)


def process_journal(records, writer, mappings):
    record, fields = majority_vote(records, ('Journal',), mappings)

    if 'issn' in record:
        uri = URIRef('urn:issn:%s' % record['issn'])
        graph_uri = URIRef('/graph/issn/%s' % record['issn'])
    elif 'x-nlm-ta' in record:
        uri = URIRef('/id/journal/%s' % sluggify(record['x-nlm-ta']))
        graph_uri = URIRef('/graph/journal/%s' % sluggify(record['x-nlm-ta']))
    elif 'name' in record:
        uri = URIRef('/id/journal/%s' % sluggify(record['name']))
        graph_uri = URIRef('/graph/journal/%s' % sluggify(record['name']))
    else:
        pass
        #print record

    for id, _ in fields['id']:
        mappings['id'][id] = uri
        mappings['journal'][uri] = graph_uri.split('/', 3)[-1]

    writer.send((uri, NS.rdf.type, FABIO.Journal, graph_uri))

    for key, predicate in JOURNAL_DATA_PROPERTIES:
        if key in record:
            writer.send((uri, predicate, Literal(record[key]), graph_uri))

    if fields['publisher']:
        pass # TODO: Unify on publisher-id from the NLM XML

def process_articles(input_filename, writer, mappings):
    tar = tarfile.open(input_filename, 'r:gz')
    for tar_info, journal in get_datasets(tar, types=('Article',)):
        process_article(journal['recordList'], writer, mappings)

def process_article(records, writer, mappings):
    record, fields = majority_vote(records, ('Article',), mappings)

    fabio_type = record.get('x-fabio-type', 'Expression')
    graph_uri_type = '-'.join(''.join(' '+c if c.isupper() else c for c in fabio_type).split())

    if 'doi' in record:
        uri = URIRef('http://dx.doi.org/%s' % record['doi'])
        uri_part = ':doi/%s' % record['doi']
    elif 'isbn' in record:
        uri = URIRef('urn:isbn:%s' % record['isbn'])
        uri_part = ':isbn/%s' % record['isbn']
    elif 'pmid' in record:
        uri = URIRef('/id/expression:pmid/%s' % record['pmid'])
        uri_part = ':pmid/%s' % record['pmid']
    else:
        id = ''.join(random.choice(string.letters) for i in range(16))
        uri = URIRef('/id/expression/%s' % id)
        uri_part = '/%s' % id

    graph_uri = URIRef('/graph/expression%s' % uri_part)
    manifestation_uri = URIRef('/graph/manifestation%s' % uri_part)

    for id, _ in fields['id']:
        mappings['id'][id] = uri
        mappings['article'][id] = uri_part

    writer.send((uri, NS.rdf.type, FABIO[record.get('x-fabio-type', 'Expression')], graph_uri))
    writer.send((uri, FRBR.embodiment, manifestation_uri, graph_uri))
    writer.send((manifestation_uri, RDF.type, FABIO.Manifestation, graph_uri))

    for key, predicate in ARTICLE_DATA_PROPERTIES:
        if key in record:
            writer.send((uri, predicate, Literal(record[key]), graph_uri))

    if 'volume' in record:
        volume_uri = URIRef('/id/journal/%s/%s' % (mappings['journal'][record['journal']], record['volume']))
        writer.send((volume_uri, NS.rdf.type, FABIO.JournalVolume, graph_uri))
        #print record['journal']
        writer.send((volume_uri, FRBR.partOf, record['journal'], graph_uri))
        writer.send((volume_uri, PRISM.volume, Literal(record['volume']), graph_uri))
    elif 'journal' in record:
        volume_uri = None
        writer.send((uri, FRBR.partOf, record['journal'], graph_uri))
    else:
        volume_uri = None
    if volume_uri and 'issue' in record:
        issue_uri = URIRef('/id/journal/%s/%s/%s' % (mappings['journal'][record['journal']], record['volume'], record['issue']))
        writer.send((issue_uri, RDF.type, FABIO.JournalIssue, graph_uri))
        writer.send((issue_uri, FRBR.partOf, volume_uri, graph_uri))
        writer.send((issue_uri, PRISM.issueIdentifier, Literal(record['issue']), graph_uri))
        writer.send((uri, FRBR.partOf, issue_uri, graph_uri))
    elif volume_uri:
        writer.send((uri, FRBR.partOf, volume_uri, graph_uri))

    if 'pageStart' in record:
        writer.send((manifestation_uri, PRISM.startingPage, Literal(record['pageStart']), graph_uri))
    if 'pageEnd' in record:
        writer.send((manifestation_uri, PRISM.endingPage, Literal(record['pageEnd']), graph_uri))

    #pprint.pprint(record)


def process_citations(input_filename, writer, mappings):
    tar = tarfile.open(input_filename, 'r:gz')
    for tar_info, journal in get_datasets(tar, types=('Article',)):
        process_citation(journal['recordList'], writer, mappings)

def process_citation(records, writer, mappings):
    record, fields = majority_vote(records, ('Article',), mappings)
    if 'cites' not in record:
        return

    article_uri = mappings['id'][record['id']]
    ref_list_uri = URIRef('/id/ref-list%s' % mappings['article'][record['id']])
    graph_uri = URIRef('/graph/ref-list%s' % mappings['article'][record['id']])
    size = len(record['cites'])

    writer.send((ref_list_uri, RDF.type, BIRO.ReferenceList, graph_uri))
    writer.send((ref_list_uri, FRBR.partOf, article_uri, graph_uri))
    writer.send((ref_list_uri, COLLECTIONS.size, Literal(size, datatype=XSD.int), graph_uri))


    for i, citation in enumerate(record['cites']):
        item_uri = URIRef('%s/%d' % (ref_list_uri, i+1))
        writer.send((article_uri, CITO.cites, citation, graph_uri))

        writer.send((ref_list_uri, COLLECTIONS.item, item_uri, graph_uri))
        if i == 0:
            writer.send((item_uri, COLLECTIONS.firstItem, item_uri, graph_uri))
        if i == size - 1:
            writer.send((item_uri, COLLECTIONS.lastItem, item_uri, graph_uri))
        if i < size - 1:
            writer.send((item_uri, COLLECTIONS.nextItem, item_uri, graph_uri))
            writer.send((item_uri, COLLECTIONS.firstItem, URIRef('%s/%d' % (ref_list_uri, i+2)), graph_uri))


        writer.send((item_uri, COLLECTIONS.itemContent, citation, graph_uri))



JOURNAL_DATA_PROPERTIES = (
    ('x-nlm-ta', FABIO.hasNationalLibraryOfMedicineJournalId),
    ('issn', PRISM.issn),
    ('eissn', PRISM.eIssn),
    ('name', DCTERMS['title']),
)

ARTICLE_DATA_PROPERTIES = (
    ('title', DCTERMS['title']),
    ('doi', PRISM.doi),
    ('pmc', FABIO.hasPubMedCentralId),
    ('pmid', FABIO.hasPubMedId),
    ('isbn', PRISM.isbn),
)

def normalize_quad(quad):
    assert len(quad) == 4, "Quad of wrong length"
    for term in quad:
        if isinstance(term, URIRef):
            yield URIRef(urljoin(BASE, term))
        else:
            yield term

def quad_writer(out):
    while True:
        quad = yield
        out.write(' '.join(term.n3().encode('utf-8') for term in normalize_quad(quad)))
        out.write(' .\n')

def run(input_filename, out):
    writer = quad_writer(out)
    writer.next()
    mappings = defaultdict(dict)
    process_journals(input_filename, writer, mappings)
    #pprint.pprint( mappings)
    process_articles(input_filename, writer, mappings)
    process_citations(input_filename, writer, mappings)


if __name__ == '__main__':
    run(sys.argv[1], sys.stdout)


