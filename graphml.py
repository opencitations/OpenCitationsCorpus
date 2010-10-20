from xml.sax import make_parser
from xml.sax.handler import ContentHandler
from xml.sax.saxutils import XMLGenerator

import networkx

__all__ = ['read_graphml']

"""
Contains a method ``read_graphml`` that takes a file-like object and returns an networkx.Graph instance.

Unlike the bundled reader, this also returns the data.
"""

_types = (
    # Name,     type,    encode, decode
    ('string',  unicode, unicode, unicode),
    ('int',     int,     unicode, int),
    ('double',  float,   unicode, float),
    ('long',    long,    unicode, long),
    ('boolean', bool,    lambda x:('true' if x else 'false'), lambda x:x == 'true'),
    ('string',  object,  unicode, unicode),
)

_type_dict = dict((x[0], x[1:]) for x in _types)

class GraphMLHandler(ContentHandler):
    def startDocument(self):
        self._context = []
        self._graph = networkx.MultiDiGraph()
        self._defaultDirected = [True]
        self._data_types = {}

        self._id = None
        self._source, self._target = None, None
        self._directed = None
        self._data = None
        self._data_key = None
        self._data_type = None

    def startElement(self, name, attrs):
        context, graph, defaultDirected = self._context, self._graph, self._defaultDirected
        attrs = dict(attrs)

        context.append(name)
        if len(context) == 1:
            if name != 'graphml':
                raise GraphFormatError, \
                      'Unrecognized outer tag "%s" in GraphML' % name
        elif len(context) == 2 and name == 'graph':
            if 'edgedefault' not in attrs:
                raise GraphFormatError, \
                      'Required attribute edgedefault missing in GraphML'
            if attrs['edgedefault'] == 'undirected':
                self._defaultDirected[0] = False

        elif len(context) == 2 and name == 'key':
            self._data_types[(attrs['for'], attrs['attr.name'])] = _type_dict[attrs['attr.type']][2]

        elif len(context) == 3 and context[1] == 'graph' and name in ('node', 'edge'):
            self._id = attrs.get('id')
            self._source, self._target = attrs.get('source'), attrs.get('target')
            self._directed = {'true':True, 'false':False}.get(attrs.get('directed'))
            self._data = {}

        elif len(context) == 4 and context[1] == 'graph' and name == 'data':
            self._data_key = attrs['key']
            self._data[self._data_key] = []
            self._data_type = self._data_types.get((context[2], attrs['key']), 'string')

    def characters(self, content):
        if self._data and self._data_key:
            self._data[self._data_key].append(content)

    def endElement(self, name):
        if name == 'data':
            value = ''.join(self._data[self._data_key]).strip()
            self._data[self._data_key] = self._data_type(value)
            self._data_key = None

        if name == 'node':
            if self._id is None:
                raise GraphFormatError, 'Required attribute edgedefault missing in GraphML'
            self._graph.add_node(self._id, attr_dict=self._data)
        if name == 'edge':
            if self._source is None:
                raise GraphFormatError, 'Edge without source in GraphML'
            if self._target is None:
                raise GraphFormatError, 'Edge without target in GraphML'

            self._graph.add_edge(self._source, self._target, attr_dict=self._data, key=self._id)
            if self._directed is False or (self._directed is None and not self._defaultDirected[-1]):
                self._graph.add_edge(self._target, self._source, attr_dict=self._data, key=self._id)

        if name in ('node', 'edge'):
            self._id, self._source, self._target, self._data, self._directed = [None for i in range(5)]

        self._context.pop()

    @property
    def graph(self):
        return self._graph

def read_graphml(f):
    handler = GraphMLHandler()
    parser = make_parser()
    parser.setContentHandler(handler)
    parser.parse(f)
    return handler.graph

class GraphMLWriter(object):
    def __init__(self, f):
        self._generator = XMLGenerator(f, 'utf-8')
        self._data_types = {}

    def write(self, graph):
        generator = self._generator

        generator.startDocument()
        generator.startElement('graphml', attrs={'xmlns': 'http://graphml.graphdrawing.org/xmlns'})

        self._write_keys(graph)


        generator.startElement('graph', attrs={'id': graph.name or '',
                                               'edgedefault': 'directed' if graph.is_directed() else 'undirected'})

        for node in graph:
            self._write_node(node, graph.node[node])

        for source, target, data in graph.edges(data=True):
            self._write_edge(source, target, data)
        
        generator.endElement('graph')

        generator.endElement('graphml')
        generator.endDocument()

    def _write_keys(self, graph):
        def write_keys(name, specimen):
            for key, value in specimen.items():
                for type_name, type_, encode, decode in _types:
                    if isinstance(value, type_):
                        break
                self._data_types[(name, key)] = encode
                self._generator.startElement('key', attrs={'for': name,
                                                           'id': key,
                                                           'attr.name': key,
                                                           'attr.type': type_name})
                self._generator.endElement('key')

        write_keys('node', graph.node[graph.nodes()[0]])
        write_keys('edge', graph.edges(data=True)[0][2])

    def _write_node(self, node, data):
        generator = self._generator

        generator.startElement('node', attrs={'id': unicode(node)})
        self._write_data('node', data)
        generator.endElement('node')

    def _write_edge(self, source, target, data):
        generator = self._generator

        generator.startElement('edge', attrs={'source': source,
                                              'target': target})
        self._write_data('edge', data)
        generator.endElement('edge')

    def _write_data(self, name, data):
        generator = self._generator

        for key, value in data.items():
            generator.startElement('data', attrs={'key': key})
            generator.characters(self._data_types[(name, key)](value))
            generator.endElement('data')



def write_graphml(f, graph):
    generator = GraphMLWriter(f)
    generator.write(graph)


if __name__ == '__main__':
    import sys
    from StringIO import StringIO

    a, b = StringIO(), StringIO()
    write_graphml(a, read_graphml('articles-Cytokine.gml'))
    a = StringIO(a.getvalue())
    write_graphml(b, read_graphml(a))

    open('a.xml', 'w').write(a.getvalue())
    open('b.xml', 'w').write(b.getvalue())
    assert(a == b)
