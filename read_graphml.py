from xml.sax import make_parser
from xml.sax.handler import ContentHandler

import networkx

__all__ = ['read_graphml']

"""
Contains a method ``read_graphml`` that takes a file-like object and returns an networkx.Graph instance.

Unlike the bundled reader, this also returns the data.
"""

class GraphMLHandler(ContentHandler):
    def startDocument(self):
        self._context = []
        self._graph = networkx.MultiDiGraph()
        self._defaultDirected = [True]

        self._id = None
        self._source, self._target = None, None
        self._directed = None
        self._data = None
        self._data_key = None

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
        elif len(context) == 3 and context[1] == 'graph' and name in ('node', 'edge'):
            self._id = attrs.get('id')
            self._source, self._target = attrs.get('source'), attrs.get('target')
            self._directed = {'true':True, 'false':False}.get(attrs.get('directed'))
            self._data = {}

        elif len(context) == 4 and context[1] == 'graph' and name == 'data':
            self._data_key = attrs['key']
            self._data[self._data_key] = []

    def characters(self, content):
        if self._data and self._data_key:
            self._data[self._data_key].append(content)

    def endElement(self, name):
        if name == 'data':
            self._data[self._data_key] = ''.join(self._data[self._data_key]).strip()
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

