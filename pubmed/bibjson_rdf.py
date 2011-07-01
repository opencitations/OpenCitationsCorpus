# coding: utf-8
from collections import defaultdict
import pprint
import gzip
import random
import re
import string
import sys
import tarfile
import traceback
from urlparse import urljoin, urlparse
from urllib import quote as urllib_quote

from rdflib import Literal, URIRef, Namespace

BASE = 'http://opencitations.net/'

YEAR_RE = re.compile(r'^-?\d{4}$')


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
    'org': 'http://www.w3.org/ns/org#',
    'ov': 'http://open.vocab.org/terms/',
    'prism': 'http://prismstandard.org/namespaces/basic/2.0/',
    'pro': 'http://purl.org/spar/pro/',
    'pso': 'http://purl.org/spar/pso/',
    'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
    'rdfs': 'http://www.w3.org/2000/01/rdf-schema#',
    'skos': 'http://www.w3.org/2004/02/skos/core#',
    'v': 'http://www.w3.org/2006/vcard/ns#',
    'xsd': 'http://www.w3.org/2001/XMLSchema#',
}
NS = type('Namespaces', (dict,), {'__getattr__': lambda self,key: self[key]})((k, Namespace(v)) for k,v in NS.items())

BIRO = NS.biro
CITO = NS.cito
COLLECTIONS = NS.collections
DCTERMS = NS.dcterms
FABIO = NS.fabio
FOAF = NS.foaf
FRBR = NS.frbr
ORG = NS.org
OV = NS.ov
PRISM = NS.prism
PRO = NS.pro
RDF = NS.rdf
RDFS = NS.rdfs
SKOS = NS.skos
VCARD = NS.v
XSD = NS.xsd

class hashabledict(dict):
    def __hash__(self):
        return hash(tuple(sorted(self.items())))
    def __setitem__(self): return NotImplemented
    def __delitem__(self): return NotImplemented

def normalize_field(value, mappings, records):
    if isinstance(value, dict) and 'ref' in value:
        ref = value['ref'][1:]
        if ref in mappings['id']:
            value = mappings['id'][ref]
        elif ref in records:
            value = records[ref]
        #value.ref = ref
    if isinstance(value, dict):
        value = hashabledict((k, normalize_field(v, mappings, records)) for k,v in value.iteritems())
    if isinstance(value, list):
        value = tuple(normalize_field(v, mappings, records) for v in value)
    return value

def quote(s):
    # Custom quote that will handle (but throw away) unicode characters
    return urllib_quote(s.encode('utf-8'))

def merge_people(person_lists, mappings, records):
    # TODO: This needs a lot more intelligence
    person_lists.sort(key=lambda ps:-len(ps))
    person_list = []
    for person in person_lists[0]:
        person_list.append(normalize_field(person, mappings, records))
    return person_list

SOURCE_WEIGHTINGS = {
    'pmc_oa': 7,
    'pmc_oa_reference': 1,
    'pubmed_api': 2,
}

def majority_vote(records, types, mappings):
    records = dict((r['id'], r) for r in records)

    fields = defaultdict(lambda:defaultdict(int))
    for record in records.itervalues():
        if record['type'] not in types:
            continue
        for field, value in record.iteritems():
            value = normalize_field(value, mappings, records)
            fields[field][value] += SOURCE_WEIGHTINGS.get(record.get('x-source-type'), 0.5)
    ret = {}
    for field, values in fields.items():
        values = fields[field] = sorted(values.iteritems(), key=lambda x:-x[1])
        ret[field] = values[0][0]

    for k in ('author', 'editor', 'translator'):
        person_lists = [r.get(k, []) for r in records.itervalues() if r.get(k)]
        if person_lists:
            ret[k] = merge_people(person_lists, mappings, records)
        elif k in ret:
            del ret[k]

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


def process_organizations(input_filename, writer, mappings):
    tar = tarfile.open(input_filename, 'r:gz')
    for tar_info, journal in get_datasets(tar, types=('Organization',)):
        process_organization(journal['recordList'], writer, mappings)

def process_organization(records, writer, mappings):
    record, fields = majority_vote(records, ('Organization',), mappings)

    uri_part = sluggify(record.get('name') or record.get('address') or 'unknown')
    mappings['orgs'][uri_part] = mappings['orgs'].get(uri_part, 0) + 1
    uri_part = "%s-%s" % (uri_part, mappings['orgs'][uri_part])
    uri = URIRef('/id/org/%s' % uri_part)
    graph_uri = URIRef('/graph/org/%s' % uri_part)

    writer.send((uri, RDF.type, ORG.Organization, graph_uri))
    if 'name' in record:
        writer.send((uri, SKOS.prefLabel, Literal(record['name']), graph_uri))
        writer.send((uri, RDFS.label, Literal(record['name']), graph_uri))
    if 'address' in record:
        address_uri = URIRef(uri + '/address')
        writer.send((uri, VCARD.adr, address_uri, graph_uri))
        writer.send((address_uri, RDF.type, VCARD.Address, graph_uri))
        writer.send((address_uri, RDFS.label, Literal(record['address']), graph_uri))

    for id, _ in fields['id']:
        mappings['id'][id] = uri


def process_journals(input_filename, writer, mappings):
    tar = tarfile.open(input_filename, 'r:gz')
    for tar_info, journal in get_datasets(tar, types=('Journal',)):
        process_journal(journal['recordList'], writer, mappings)


def process_journal(records, writer, mappings):
    record, fields = majority_vote(records, ('Journal',), mappings)

    if record.get('issn'):
        uri = URIRef('urn:issn:%s' % record['issn'])
        graph_uri = URIRef('/graph/issn/%s' % record['issn'])
    elif record.get('x-nlm-ta'):
        uri = URIRef('/id/journal/%s' % sluggify(record['x-nlm-ta']))
        graph_uri = URIRef('/graph/journal/%s' % sluggify(record['x-nlm-ta']))
    elif record.get('name'):
        uri = URIRef('/id/journal/%s' % sluggify(record['name']))
        graph_uri = URIRef('/graph/journal/%s' % sluggify(record['name']))
    else:
        sys.stderr.write("Unidentifiable: %s" % record)
        return

    for id, _ in fields['id']:
        mappings['id'][id] = uri
        mappings['journal'][uri] = graph_uri.split('/', 3)[-1]

    writer.send((uri, RDF.type, FABIO.Journal, graph_uri))

    for key, predicate in JOURNAL_DATA_PROPERTIES:
        if key in record:
            writer.send((uri, predicate, Literal(record[key]), graph_uri))

    if isinstance(record.get('publisher'), URIRef):
        writer.send((uri, DCTERMS.publisher, record['publisher'], graph_uri))

def uriencode_doi(doi):
    s = []
    for c in doi:
        if c in encode_characters:
            s.append('%%%02X' % ord(c))
        else:
            s.append(c)
    return u''.join(s)
encode_characters = set(unichr(i) for i in range(0x20)) | set(u'\x7f #%"<>')

def process_articles(input_filename, writer, mappings):
    tar = tarfile.open(input_filename, 'r:gz')
    for tar_info, journal in get_datasets(tar, types=('Article',)):
        try:
            process_article(journal['recordList'], writer, mappings)
        except Exception:
            traceback.print_exc(file=sys.stderr)

def process_article(records, writer, mappings):
    record, fields = majority_vote(records, ('Article',), mappings)

    fabio_type = record.get('x-fabio-type', 'Expression')
    graph_uri_type = '-'.join(''.join(' '+c if c.isupper() else c for c in fabio_type).split())

    if fabio_type in ('WebPage', 'WebSite') and record.get('url'):
        uri = URIRef(record['url'])
        uri_part = u':web/%s' % quote(record['url'])
    elif 'doi' in record:
        uri = URIRef(u'http://dx.doi.org/' + uriencode_doi(record['doi']))
        uri_part = u':doi/%s' % uriencode_doi(record['doi'])
    elif 'isbn' in record:
        uri = URIRef('urn:isbn:%s' % record['isbn'])
        uri_part = u':isbn/%s' % record['isbn']
    elif 'pmid' in record:
        uri = URIRef('/id/expression:pmid/%s' % record['pmid'])
        uri_part = u':pmid/%s' % record['pmid']
    else:
        id = ''.join(random.choice(string.letters) for i in range(16))
        uri = URIRef('/id/expression/%s' % id)
        uri_part = u'/%s' % id

    graph_uri = URIRef('/graph/expression%s' % uri_part)
    manifestation_uri = URIRef('/id/manifestation%s' % uri_part)
    abstract_uri = URIRef('/id/abstract%s' % uri_part)

    if fabio_type in ('WebPage', 'WebSite') and record.get('url'):
        writer.send((uri, RDF.type, FOAF.Document, graph_uri))

    if 'url' in record and unicode(uri) != record['url']:
        url = URIRef(record['url'])
        try:
            fabio_type = FABIO.WebSite if urlparse(url).path == '/' else FABIO.WebPage
        except Exception:
            sys.stderr.write('Invalid URL: %r\n' % url)
        else:
            writer.send((url, RDF.type, fabio_type, graph_uri))
            writer.send((url, RDF.type, FOAF.Document, graph_uri))
            writer.send((url, FOAF.primaryTopic, uri, graph_uri))
            writer.send((uri, FOAF.primaryTopicOf, url, graph_uri))

    for id, _ in fields['id']:
        mappings['id'][id] = uri
        mappings['article'][id] = uri_part

    writer.send((uri, RDF.type, FABIO[record.get('x-fabio-type', 'Expression')], graph_uri))
    writer.send((uri, FRBR.embodiment, manifestation_uri, graph_uri))
    writer.send((manifestation_uri, RDF.type, FABIO.Manifestation, graph_uri))

    for key, predicate in ARTICLE_DATA_PROPERTIES:
        if record.get(key):
            writer.send((uri, predicate, Literal(record[key]), graph_uri))

    if 'volume' in record and isinstance(record.get('journal'), URIRef):
        volume_uri = URIRef('/id/journal/%s/%s' % (mappings['journal'][record['journal']], sluggify(record['volume'])))
        writer.send((volume_uri, RDF.type, FABIO.JournalVolume, graph_uri))
        #print record['journal']
        writer.send((record['journal'], FRBR.part, volume_uri, graph_uri))
        writer.send((volume_uri, PRISM.volume, Literal(record['volume']), graph_uri))
    elif isinstance(record.get('journal'), URIRef):
        volume_uri = None
        writer.send((record['journal'], FRBR.part, uri, graph_uri))
    else:
        volume_uri = None
    if volume_uri and 'issue' in record:
        issue_uri = URIRef('/id/journal/%s/%s/%s' % (mappings['journal'][record['journal']], sluggify(record['volume']), sluggify(record['issue'])))
        writer.send((issue_uri, RDF.type, FABIO.JournalIssue, graph_uri))
        writer.send((volume_uri, FRBR.part, issue_uri, graph_uri))
        writer.send((issue_uri, PRISM.issueIdentifier, Literal(record['issue']), graph_uri))
        writer.send((issue_uri, FRBR.part, uri, graph_uri))
    elif volume_uri:
        writer.send((volume_uri, FRBR.part, uri, graph_uri))

    pageStart, pageEnd = record.get('pageStart'), record.get('pageEnd')
    if pageStart:
        writer.send((manifestation_uri, PRISM.startingPage, Literal(pageStart), graph_uri))
    if pageEnd:
        writer.send((manifestation_uri, PRISM.endingPage, Literal(pageEnd), graph_uri))
    if 'abstract' in record:
        writer.send((abstract_uri, RDF.type, FABIO.Abstract, graph_uri))
        writer.send((uri, FRBR.part, abstract_uri, graph_uri))
        writer.send((abstract_uri, RDF.value, Literal(record['abstract']), graph_uri))

        writer.send((abstract_uri, DCTERMS['title'], Literal('Abstract'), graph_uri))
        if record.get('title'):
            writer.send((abstract_uri, RDFS.label, Literal('Abstract for "%s"' % record['title']), graph_uri))

    if YEAR_RE.match(record.get('year', '')):
        date = [record['year']]
        for field_name in ('month', 'day'):
            try:
                date.append('%02d' % int(record[field_name]))
            except (KeyError, ValueError):
                date.append('01')
        writer.send((uri, DCTERMS.published, Literal('-'.join(date), datatype=XSD.date), graph_uri))
        writer.send((uri, PRISM.publicationDate, Literal('-'.join(date)+'T00:00:00Z', datatype=XSD.dateTime), graph_uri))


    for k in ('author', 'editor', 'translator'):
        for i, person in enumerate(record.get(k, [])):
            person_uri = URIRef('/graph/person%s/%s/%d' % (uri_part, k, i+1))
            role_uri = URIRef('/graph/person%s/%s/%d/role' % (uri_part, k, i+1))
            process_person(person_uri, person, graph_uri, writer, mappings)
            writer.send((uri, DCTERMS.creator if k == 'author' else DCTERMS.contributor, person_uri, graph_uri))
            writer.send((role_uri, RDF.type, PRO.RoleInTime, graph_uri))
            writer.send((person_uri, PRO.holdsRoleInTime, role_uri, graph_uri))
            writer.send((role_uri, PRO.withRole, PRO[k], graph_uri))
            writer.send((uri, PRO.isRelatedToRoleInTime, role_uri, graph_uri))
            if isinstance(person, dict) and person.get('affiliated'):
                writer.send((role_uri, PRO.withAffiliation, person['affiliated'], graph_uri))


def process_person(person_uri, person, graph_uri, writer, mappings):
    # Something's already processed it; it's probably an organization
    if isinstance(person, URIRef):
        return
    writer.send((person_uri, RDF.type, FOAF.Person, graph_uri))

    name_style = person.get('x-name-style', 'western')
    given_names = person.get('x-given-names')
    surname = person.get('x-surname')
    sort_name = name = person.get('name')

    if given_names and surname:
        # See <http://dtd.nlm.nih.gov/publishing/tag-library/n-gth0.html> for
        # details of name styles
        if name_style == 'western':
            first_name, last_name = given_names, surname
            sort_name = "%s, %s" % (surname, given_names)
        elif name_style == 'eastern':
            first_name, last_name = surname, given_names
            sort_name = "%s, %s" % (surname, given_names)
        elif name_style == 'islensk':
            first_name, last_name = given_names, surname
            sort_name = "%s, %s" % (given_names, surname)
        else:
            raise Warning("Unexpected name style")

        name = "%s %s" % (first_name, last_name)

        writer.send((person_uri, FOAF.givenName,  Literal(given_names), graph_uri))
        writer.send((person_uri, FOAF.familyName, Literal(surname), graph_uri))
        writer.send((person_uri, FOAF.firstName,  Literal(first_name), graph_uri))
        writer.send((person_uri, FOAF.lastName,  Literal(last_name), graph_uri))

    if sort_name != name:
        writer.send((person_uri, OV.sortLabel,  Literal(sort_name), graph_uri))
    writer.send((person_uri, RDFS.label, Literal(name), graph_uri))
    writer.send((person_uri, FOAF.name, Literal(name), graph_uri))

def process_citations(input_filename, writer, mappings):
    tar = tarfile.open(input_filename, 'r:gz')
    for tar_info, journal in get_datasets(tar, types=('Article',)):
        process_citation(journal['recordList'], writer, mappings)

def process_citation(records, writer, mappings):
    record, fields = majority_vote(records, ('Article',), mappings)

    article_uri = mappings['id'][record['id']]
    ref_list_uri = URIRef('/id/ref-list%s' % mappings['article'][record['id']])
    graph_uri = URIRef('/graph/ref-list%s' % mappings['article'][record['id']])

    for i, retration in enumerate(record.get('retracts', ())):
        writer.send((article_uri, CITO.retracts, retraction, graph_uri))
        mappings['pso'][retraction]

    if 'cites' not in record:
        return

    citing_record = (r for r in records if r.get('cites')).next()

    size = len(record['cites'])

    writer.send((ref_list_uri, RDF.type, BIRO.ReferenceList, graph_uri))
    writer.send((article_uri, FRBR.part, ref_list_uri, graph_uri))
    writer.send((ref_list_uri, COLLECTIONS.size, Literal(size, datatype=XSD.int), graph_uri))

    writer.send((ref_list_uri, DCTERMS['title'], Literal('References'), graph_uri))
    if record.get('title'):
        writer.send((ref_list_uri, RDFS.label, Literal('Reference list for "%s"' % record['title']), graph_uri))

    for i, citation in enumerate(record['cites']):
        item_uri = URIRef('%s/%d' % (ref_list_uri, i+1))
        writer.send((article_uri, CITO.cites, citation, graph_uri))
        writer.send((item_uri, RDF.type, COLLECTIONS.Item, graph_uri))

        writer.send((ref_list_uri, COLLECTIONS.item, item_uri, graph_uri))
        if i == 0:
            writer.send((ref_list_uri, COLLECTIONS.firstItem, item_uri, graph_uri))
        if i == size - 1:
            writer.send((ref_list_uri, COLLECTIONS.lastItem, item_uri, graph_uri))
        if i < size - 1:
            writer.send((URIRef('%s/%d' % (ref_list_uri, i+2)), COLLECTIONS.previousItem, item_uri, graph_uri))
            writer.send((item_uri, COLLECTIONS.nextItem, URIRef('%s/%d' % (ref_list_uri, i+2)), graph_uri))

        writer.send((item_uri, COLLECTIONS.itemContent, citation, graph_uri))

#        mappings['citing'][citation.ref] = (item_uri, citing_record['id'])


def process_errors(input_filename, writer, mappings):
    tar = tarfile.open(input_filename, 'r:gz')
    for tar_info, dataset in get_datasets(tar, types=None):
        process_error(dataset['recordList'], writer, mappings)

def process_error(records, writer, mappings):
    for record in records:
        errors = record.get('x-errors')
        if not errors:
            continue




JOURNAL_DATA_PROPERTIES = (
    ('x-nlm-ta', DCTERMS.identifier),
    ('x-nlm-id', FABIO.hasNationalLibraryOfMedicineJournalId),
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

#PERSON_OBJECT_PROPERTIES = (
#    ('author', 

def normalize_quad(quad):
    assert len(quad) == 4, "Quad of wrong length"
    for term in quad:
        if isinstance(term, URIRef):
            if not term.startswith(u'urn:') and not term.startswith(u'http:'):
                yield URIRef(u'http://opencitations.net' + term).n3()
            else:
                yield term.n3()
            #yield URIRef(urljoin(BASE, term)).n3()
            continue
        value = u'"%s"' % term.strip().replace(u'\\', ur'\\').replace(u'\n', ur'\n').replace(u'"', ur'\"')
        if term.language:
            value += u'@' + term.language
        elif term.datatype:
            value += u'^^' + term.datatype.n3()
        yield value

def quad_writer(out):
    queue = []
    while True:
        quad = yield
        if quad is None:
            break
        try:
            queue.append(' '.join(term.encode('utf-8') for term in normalize_quad(quad)))
            queue.append(' .\n')
        except Exception:
            traceback.print_exc(file=sys.stderr)
        if len(queue) > 128:
            out.write(''.join(queue))
            queue[:] = []
    out.write(''.join(queue))


def run(input_filename, out):
    writer = quad_writer(out)
    writer.next()
    mappings = defaultdict(dict)

    sys.stderr.write('1. Organizations\n')
    process_organizations(input_filename, writer, mappings)
    sys.stderr.write('2. Journals\n')
    process_journals(input_filename, writer, mappings)
    sys.stderr.write('3. Articles\n')
    process_articles(input_filename, writer, mappings)
    sys.stderr.write('4. Citations\n')
    process_citations(input_filename, writer, mappings)
    #sys.stderr.write('5. Errors\n')
    #process_errors(input_filename, writer, mappings)

    try:
        writer.send(None)
    except StopIteration:
        pass


if __name__ == '__main__':
    import cProfile
    def f():
        try:
            run(sys.argv[1], sys.stdout)
        except KeyboardInterrupt:
            pass
    f = gzip.GzipFile('../parsed/articles.nq.gz', 'w')
    run('../parsed/articles-unified.bibjson.tar.gz', f)
    f.close()

    #cProfile.run('f()', 'profile.stats')


