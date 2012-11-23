import os, stat, traceback, sys
from collections import defaultdict
from pprint import pprint
import psycopg2
from graphml import read_graphml

conn = psycopg2.connect("dbname=pubmed user=pubmed password=pubmed")


def create_table(cursor, name, create):
    cursor.execute("select * from information_schema.tables where table_name=%s", (name,))
    if cursor.rowcount:
        cursor.execute('DROP TABLE %s CASCADE' % name)
    cursor.execute(create)

def create_tables(cursor):
    create_table(cursor, 'article', """\
        CREATE TABLE article (
            id VARCHAR(128) PRIMARY KEY,
            container VARCHAR(64),
            ctype VARCHAR(128),
            journal VARCHAR(128),
            doi VARCHAR(128),
            pmid VARCHAR(32),
            pmc VARCHAR(16),
            isbn VARCHAR(13),
            full_citation TEXT,
            year VARCHAR(32),
            month smallint,
            day smallint,
            title VARCHAR(2048),
            author VARCHAR(4096),
            source VARCHAR(2048),
            publisher VARCHAR(2048),
            issue VARCHAR(64),
            volume VARCHAR(64),
            edition VARCHAR(64)
        )""")
    create_table(cursor, 'citation', """\
        CREATE TABLE citation (
            id VARCHAR(128) PRIMARY KEY,
            source VARCHAR(128) REFERENCES article,
            target VARCHAR(128) REFERENCES article,
            count smallint,
            paragraphs TEXT
        )""")

lengths = {'id': 128, 'container': 64, 'ctype': 128, 'journal': 128, 'doi': 128, 'pmid': 32, 'pmc': 16, 'isbn': 13, 'year': 32, 'title': 2048, 'author': 4096, 'source': 2048, 'publisher': 2048, 'issue': 64, 'volume': 64, 'edition': 64}

def get_graphs():
    directories = sorted(os.listdir('out'), key=lambda x:max([0]+[os.stat(os.path.join('out', x, y))[stat.ST_MTIME] for y in os.listdir(os.path.join('out', x))]), reverse=True)
    for directory in directories:
        for filename in os.listdir(os.path.join('out', directory)):
            filename = os.path.join('out', directory, filename)
            if filename.endswith('.xml'):
                try:
                    yield directory, read_graphml(filename)
                except Exception:
                    traceback.print_exc(file=sys.stderr)
                    pass


cursor = conn.cursor()

create_tables(cursor)

i, last_journal, j = 0, None, 0
for journal, graph in get_graphs():
    j += 1
    if journal != last_journal:
        if last_journal:
            print "%4d %4d %s" % (i, j, last_journal)
        i += 1
        last_journal, j = journal, 0
        print
    if j % 100 == 0:
        print "%4d %4d %s" % (i, j, journal)
    nodes = []
    for id_, data in graph.nodes(data=True):
        data = defaultdict(lambda:None, data)
        data['id'] = id_
        data['journal'] = journal
        data['container'] = data.pop('_xml_container')
        for k in list(data):
            if data[k] == '':
                del data[k]
            if isinstance(data[k], basestring) and len(data[k]) > lengths.get(k, 10000000):
                print "Trimming %s from %s (%d/%d): %r" % (k, journal, len(data[k]), lengths[k], data[k])
                data[k] = data[k][:lengths[k]]

        nodes.append(data)

    edges = []
    for source, target, data in graph.edges(data=True):
        data = defaultdict(lambda:None, data)
        data['id'] = data['target'] = target
        data['source'] = source
        for k in list(data):
            if data[k] == '':
                del data[k]
        edges.append(data)

    for k in range(0, len(nodes), 100):
        nodegroup = nodes[k:k+100]
        try:
            cursor.execute("INSERT INTO article VALUES %s" % ', '.join(cursor.mogrify("""(
                %(id)s, %(_xml_countainer)s, %(ctype)s, %(journal)s, %(doi)s,
                %(pmid)s, %(pmc)s, %(isbn)s, %(full_citation)s, %(year)s,
                %(month)s, %(day)s, %(title)s, %(author)s, %(source)s,
                %(publisher)s, %(issue)s, %(volume)s, %(edition)s)""", n) for n in nodegroup))
        except Exception:
            print nodes
            traceback.print_exc(file=sys.stderr)
    for k in range(0, len(edges), 100):
        edgegroup = edges[k:k+100]
        try:
            cursor.execute("INSERT INTO citation VALUES %s" % ', '.join(cursor.mogrify("(%(id)s, %(source)s, %(target)s, %(count)s, %(paragraphs)s)", e) for e in edgegroup))
        except Exception:
            print edges
            traceback.print_exc(file=sys.stderr)

    conn.commit()

conn.commit()
