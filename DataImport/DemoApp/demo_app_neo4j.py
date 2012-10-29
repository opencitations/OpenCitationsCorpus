# Fix neo4j java bindings
import os, sys
os.environ['NEO4J_PYTHON_JVMARGS'] = '-Xms512M -Xmx1024M'
os.environ['CLASSPATH'] = '/usr/lib/jvm/java-6-openjdk/jre/lib/'
os.environ['JAVA_HOME'] = '/usr/lib/jvm/java-6-openjdk/jre/'
sys.path.append(os.getcwd())

from BaseHTTPServer import BaseHTTPRequestHandler
from neo4j import GraphDatabase

from urlparse import urlparse, parse_qs
from urllib import unquote

from pages import get_front_page, get_paper_page, get_search_page, get_autor_page

# Debugger
import ipdb
BREAK = ipdb.set_trace

def application(environ, start_response):
    '''Serve Related-Work.net to Apache mod-WSGI'''
    sys.stdout = environ['wsgi.errors']
    try: 
        db
    except NameError:
        print "##################### RESTART #######################"
        print "Initializing db. From PID %d in dir %s" % (os.getpid(), os.getcwd())
        init_globals()
        
    status = '200 OK' 
    output = get_html(environ['REQUEST_URI'])
    response_headers = [('Content-type', 'text/html'),
                        ('Content-Length', str(len(output)))]
    start_response(status, response_headers)

    return [output]

def main():
    '''Serve Related-Work.net on http://localhost:8000'''
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
def get_html(url_string):
    '''Related-Work url switch table'''

    print 'called:', url_string
    url = urlparse(url_string)
    path = unquote(url.path).decode('utf8')
    query_dict = parse_qs(url.query)

    print url, path, query_dict

    if path.endswith('.ico'): return ''
    if path == '/':
        return get_front_page()
    if path == '/search':
        try:
            search_string = query_dict['q'][0]
        except (KeyError, IndexError):
            search_string = ''
        return get_search_page(search_string, search_idx)
    if path.startswith('/author/'):
        return get_autor_page(path.split('/')[-1], author_idx)

    # Get paper_node
    rw_id = path.split('/')[-1]
    rw_id = rw_id.replace('_','/')
    for paper_node in source_idx['id'][rw_id]:
        break
    else:
        return "Id %s not found" % rw_id

    return get_paper_page(paper_node)



class MyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            self.send_response(200)
            self.send_header('Content-type',	'text/html')
            self.end_headers()
            self.wfile.write(get_html(self.path))
        except IOError:
            self.send_error(404,'File Not Found: %s' % self.path)


if __name__ == '__main__':
    main()

