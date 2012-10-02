import os, sys
os.environ['NEO4J_PYTHON_JVMARGS'] = '-Xms512M -Xmx1024M'
os.environ['CLASSPATH'] = '/usr/lib/jvm/java-6-openjdk/jre/lib/'
os.environ['JAVA_HOME'] = '/usr/lib/jvm/java-6-openjdk/jre/'

from itertools import islice
from os import curdir, sep
from re import findall, sub
from urllib import unquote
from BaseHTTPServer import BaseHTTPRequestHandler
from neo4j import GraphDatabase
from unicodedata import normalize
from templates import (front_html, main_template,
                       author_template, search_template,
                       html_head)

def application(environ, start_response):
    # to be called from Apache mod-WSGI
    sys.stdout = environ['wsgi.errors']
    try: 
        db
    except:
        print "##################### RESTART #######################"
        print "Initializing db. From PID %d in dir %s" % (os.getpid(), os.getcwd())
        init_globals()
        
    status = '200 OK' 
    output = get_html(environ['PATH_INFO'])
    response_headers = [('Content-type', 'text/html'),
                        ('Content-Length', str(len(output)))]
    start_response(status, response_headers)

    return [output]


def main():
    # serve stand alone server if called from the command line
    from BaseHTTPServer import HTTPServer
    init_globals()

    try:
        server = HTTPServer(('', 8000), MyHandler)
        print 'Welcome to the machine...'
        server.serve_forever()
    except:
        print '^C received, shutting down server'
        db.shutdown()
        server.socket.close()


class MyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            self.send_response(200)
            self.send_header('Content-type',	'text/html')
            self.end_headers()
            self.wfile.write(get_html(self.path))
        except IOError:
            self.send_error(404,'File Not Found: %s' % self.path)


def init_globals():
    '''Restore global varibales on a running db'''
    global db
    global ROOT, PAPER, AUTHOR
    global author_idx, source_idx, label_idx, search_idx

    db = GraphDatabase('db_folder')
    
    label_idx  = db.node.indexes.get('label_idx')
    source_idx = db.node.indexes.get('source_idx')
    author_idx = db.node.indexes.get('author_idx')
    search_idx = db.node.indexes.get('search_idx')
    
    AUTHOR = label_idx['label']['AUTHOR'].single
    PAPER  = label_idx['label']['PAPER'].single
    ROOT   = db.reference_node


class CacheDecorator():
	def __init__ (self, f):
		self.f = f
		self.mem = {}
	def __call__ (self, *args, **kwargs):
		if (args, str(kwargs)) in self.mem:
			return self.mem[args, str(kwargs)]
		else:
			tmp = self.f(*args, **kwargs)
			self.mem[args, str(kwargs)] = tmp
			return tmp

@CacheDecorator
def get_html(path):
    print 'called:', path
    if path.endswith('.ico'): return ''
    if path == '/':
        return get_front_page()
    if path.startswith('/search?q='):
        return get_search_page(path.split('?q=')[-1])
    if path.split('/')[-2] == 'author':
        return get_autor_page(path.split('/')[-1])
        
    RW_ID = path.split('/')[-1]
    RW_ID=RW_ID.replace('_','/')

    for paper_node in source_idx['id'][RW_ID]:
        break
    else:
        return "Id %s not found" % RW_ID


    ref_list = [ (get_ref_html(ref.endNode),ref.endNode['c_citation_count']) for ref in islice(paper_node.ref.outgoing,0,50) ]
    # sort by cite rank
    ref_list = sorted( ref_list, key = lambda x: x[1], reverse=True)
    ref_string = '<ul>'
    ref_string += '\n'.join( entry[0] for entry in ref_list )
    ref_string += '\n'.join( '<li>' + u_ref_string + '</li>' for u_ref_string in paper_node['unknown_references'][1:] )
    ref_string += '</ul>'

    cite_list = [ (get_ref_html(ref.startNode),ref.startNode['c_citation_count']) for ref in islice(paper_node.ref.incoming,0,50) ]
    # sort by cite rank
    cite_list = sorted( cite_list, key = lambda x: x[1], reverse=True)
    cite_string = '<ul>'
    cite_string += '\n'.join([ entry[0] for entry in cite_list ])
    cite_string += '</ul>'

    html = main_template.format(
        node_id         = RW_ID,
        short_id        = RW_ID.split(':')[-1],
        source_url      = paper_node['source_url'],
        title           = paper_node['title'],
        abstract        = paper_node['abstract'],
        author          = get_author_html(paper_node),
        references      = ref_string,
        citations       = cite_string,
        citation_count  = paper_node['c_citation_count'],
        reference_count = paper_node['c_reference_count'],
        )
        
    return to_ascii(html_head + html)


def get_author_html(paper_node):
    authors = paper_node['c_authors'].split(" and ")
    authors.sort()
    return ' and '.join(
        u'''<a href="{href}"> {name} </a>'''.format(
            href = '/author/'+name.replace(' ','_'),
            name = abbrev_full_name(name))
        for name in authors)


def get_ref_html(node):
    return to_ascii(u'''
           <li><a href="{href}">{authors}, {title}, {year} (citations: {citation_count})</a></li> \n
    '''.format(
            href           = '/' + node['source_id'].replace('/','_'),
            authors        = get_author_names(node),
            title          = node['title'],
            year           = node['date'][0:4],
            citation_count = node['c_citation_count'],
            cite_rank      = node['c_cite_rank']
            ))

def get_author_names(paper_node):
    authors = paper_node['c_authors'].split(" and ")
    authors.sort()
    authors = [ abbrev_full_name(name)  for name in authors ]
    html = ' and '.join(authors[:3])
    if len(authors) > 3:
        html += ' et.al.'
    return html


def abbrev_full_name(name):
    sir_name = name.split(', ')[0]
    rest     = ','.join(name.split(', ')[1:])
    abbrev_first_name = ' '.join( " " + first_name[0] +'.' for first_name in findall(r"[a-zA-Z]+",rest))
    return sir_name + ' ' + abbrev_first_name


def to_ascii(string):
    try:
        out= normalize('NFKD', string).encode('ascii','ignore')
    except TypeError:
        out= string
    return out


def get_search_page(search_string, limit = 10):
    search_string = unquote(search_string).decode('utf8')
    search_string  = sub('\W+',' AND ', search_string)
    author_html = u'<ul>'
    for author_node in islice(search_idx.query('author',search_string),0,limit): 
        author_html += u'''<li> <a href='%s'> %s </a> </li>''' % ("/author/" + author_node['name'].replace(' ','_'), author_node['name'] )
    author_html += '</ul>'
    
    paper_html = u'<ul>'
    for paper_node in sorted(islice(search_idx.query('title', search_string),0,limit), key = lambda node: node['c_citation_count'], reverse=True):
        paper_html += get_ref_html(paper_node)
    paper_html += u'</ul>'

    html = search_template.format(
        search_string = search_string,
        authors = author_html,
        articles = paper_html
        )
    

    return to_ascii(html_head + html)
    

def get_autor_page(author_name):
    author_name = author_name.replace('_',' ')
    for author_node in author_idx['name'][author_name]: break
    else: return "Author %s not found" % author_name

    ref_list = [ (get_ref_html(ref.startNode),ref.startNode['c_citation_count']) for ref in author_node.author.incoming ]
    # sort by date
    ref_list = sorted( ref_list, key = lambda x: x[1], reverse=True)
    ref_string = '<ul>'
    ref_string += '\n'.join( entry[0] for entry in ref_list )
    ref_string += '</ul>'

    html = author_template.format(
        author_name = author_name,
        author_url  = '#',
        references = ref_string,
        )       

    return to_ascii(html_head + html)


def get_front_page():
    return to_ascii(html_head + front_html)



if __name__ == '__main__':
    main()

