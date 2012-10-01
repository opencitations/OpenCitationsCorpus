import os, sys
os.environ['NEO4J_PYTHON_JVMARGS'] = '-Xms512M -Xmx1024M'
os.environ['CLASSPATH'] = '/usr/lib/jvm/java-6-openjdk/jre/lib/'
os.environ['JAVA_HOME'] = '/usr/lib/jvm/java-6-openjdk/jre/'

from os import curdir, sep
from re import findall
from BaseHTTPServer import BaseHTTPRequestHandler
from neo4j import GraphDatabase
from unicodedata import normalize

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
    try:
        init_globals()
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
    global author_idx, source_idx, label_idx

    db = GraphDatabase('db_folder')
    
    label_idx  = db.node.indexes.get('label_idx')
    source_idx = db.node.indexes.get('source_idx')
    author_idx = db.node.indexes.get('author_idx')
    
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
    if path.split('/')[-2] == 'author':
        return get_autor_page(path.split('/')[-1])
        
    RW_ID = path.split('/')[-1]
    RW_ID=RW_ID.replace('_','/')

    for paper_node in source_idx['id'][RW_ID]:
        break
    else:
        return "Id %s not found" % RW_ID


    ref_list = [ (get_ref_html(ref.endNode),ref.endNode['c_citation_count']) for ref in paper_node.ref.outgoing ]
    # sort by cite rank
    ref_list = sorted( ref_list, key = lambda x: x[1], reverse=True)
    ref_string = '<ul>'
    ref_string += '\n'.join( entry[0] for entry in ref_list )
    ref_string += '\n'.join( '<li>' + u_ref_string + '</li>' for u_ref_string in paper_node['unknown_references'][1:] )
    ref_string += '</ul>'

    cite_list = [ (get_ref_html(ref.startNode),ref.startNode['c_citation_count']) for ref in paper_node.ref.incoming ]
    # sort by cite rank
    cite_list = sorted( cite_list, key = lambda x: x[1], reverse=True)
    cite_string = '<ul>'
    cite_string += '\n'.join([ entry[0] for entry in cite_list ])
    cite_string += '</ul>'

    html = html_template.format(
        node_id         = RW_ID,
        short_id        = RW_ID.split(':')[-1],
        source_url      = paper_node['source_url'],
        titel           = paper_node['title'],
        abstract        = paper_node['abstract'],
        author          = get_author_html(paper_node),
        references      = ref_string,
        citations       = cite_string,
        citation_count  = paper_node['c_citation_count'],
        reference_count = paper_node['c_reference_count'],
        )
        
    return to_ascii(css + analytics + html)


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

    return to_ascii(css + analytics + html)


def get_front_page():
    html =front_template.format(
        title = '<a href="#">Related-Work.net</a>',
        author = '<a href="http://heinrich-hartmann.net"> Hartmann, Heinrich</a> and <a href="http://rene-pickhardt.de">Pickhardt, Rene</a>',
        abstract = '''
This is an inofficial demo of our web project <a href='http://blog.related-work.net'>related-work.net</a>. 
The ultimate aim is to create a new website for the scientific community which brings together people reading the same article. 
An essential feature is the availability of reference data, which allows the user to find related work easily. 
So far we have extracted reference data from the <a href='http://arxiv.org'>arxiv</a> and made it browsable. Currently our database contains:
<ul>
<li>ca. 750.000 articles</li>
<li>ca. 16.000.000 reference entries </li>
<li>ca. 2.000.000 links between articles.</li>
</ul>
We follow a strict openness principle by making available the <a href='http://code.google.com/p/reference-retrieval/'> source code </a> and 
the data we collect.  For further information we kindly refer you to our <a href='http://blog.related-work.net'>proposal</a>.''',
        examples = '''
<ul>
<li><a href="http://dev.related-work.net/author/Kontsevich,_Maxim"> Author: Kontsevich, Maxim </a></li>
<li><a href="http://dev.related-work.net/author/Witten,_Edward"> Author: Witten, Edward</a></li>
<li><a href="/arxiv:hep-th_9711200">Maldacena  J.  M., The Large N Limit of Superconformal Field Theories and Supergravity, 1997 (citations: 2992)</a></li> 
<li><a href="/arxiv:hep-th_9802150">Witten  E., Anti De Sitter Space And Holography, 1998 (citations: 2448)</a></li> 
<li><a href="/arxiv:hep-th_9802109">Gubser  S.  S. and Klebanov  I.  R. and Polyakov  A.  M., Gauge Theory Correlators from Non-Critical String Theory, 1998 (citations: 2207)</a></li> 
</ul>
'''
        )

    return to_ascii(css + analytics + html)




mathjax = '''
<script type="text/x-mathjax-config">
MathJax.Hub.Config({
  tex2jax: {inlineMath: [['$','$'], ['\\(','\\)']]},
  "HTML-CSS": {scale: 90},
  ignoreClass: "references",
  processClass: "mathjax",
});
</script>
<script type="text/javascript"
  src="http://cdn.mathjax.org/mathjax/latest/MathJax.js?config=TeX-AMS-MML_HTMLorMML">
</script>
'''

css = '''
<style type="text/css">
<!--
body {
margin:0;
padding: 0;
}


h1 {
font-size:30px; font-family: 'Lucida Grande', helvetica, arial, verdana, sans-serif;
font-size: x-large;
font-weight: bold;
line-height: 150%;
}

h2 {
font-family: 'Lucida Grande', helvetica, arial, verdana, sans-serif;
font-size: medium;
line-height: 180%;
}

.text {
font-family: 'Lucida Grande', helvetica, arial, verdana, sans-serif;
font-size: 90%;
line-height: 130%;
}

#abstract {
width: 100%;
text-align:justify;
}

h2.abstract {
display: inline;
line-height: 100%;
}

a:link { color:#000070; text-decoration:none; }
a:hover { text-decoration:underline; }
a:visited { color:#551A8B; text-decoration:none; }


#meta {
   width: 80%;
   margin-top:50px;
   align : center;
}

#headder {
padding: 8px;
border-style: none none dotted none;
border-width: 2px;
background-color: #EEEEEE;
}

.references {
font-family: 'Lucida Grande', helvetica, arial, verdana, sans-serif;
font-size: 90%;
line-height: 130%;
text-align:left;
float:left; 
width:100%;
} 

.references ul {
margin: 0;
}
.references ul li {
margin-top: 5;
}

--> 
</style>'''



author_template = u'''
<body>
<div id='headder'>
    <h1 style='display:inline'> <a href='http://dev.related-work.net'>Related-Work.net</a> </h1> 
    <h2 style='display:inline'>
      >
      author
      >
      <a href='{author_url}'> {author_name} </a>
    </h2>
</div>
<div align='center' id='body'>
    <div id='meta'>
         <h1 class='tex2jax_process'>{author_name}</h1>
         <div class='references'>
              <h2>Articles:</h2>
              {references}
         </div>
    </div>
</div>
</body>
'''


front_template = u'''
<body class="tex2jax_ignore">
<div id='headder'>
    <h1 style='display:inline'> <a href='http://dev.related-work.net'>Related-Work.net</a> </h1> 
</div>
<div align='center' id='body'>
    <div id='meta'>
         <h1 class='tex2jax_process'>{title}</h1>
         <h2>by:{author}</h2>
         <div id='abstract' class='tex2jax_process'>
             <h2 class='abstract'>Abstract:</h2>{abstract}
         </div>
         <div>
         <div class='references'>
              <h2>Examples:</h2>
              {examples}
         </div>
         <div>

    </div>
</div>
</body>
'''


html_template = u'''
<body class="tex2jax_ignore">
<div id='headder'>
    <h1 style='display:inline'> <a href='http://dev.related-work.net'>Related-Work.net</a> </h1> 
    <h2 style='display:inline'> 
      >
      arxiv
      >
      <a href='#'>{short_id}</a>
    </h2>
    
    <h2 style='display:inline; float:right; line-height:100%'><a href='{source_url}'> source </a></h2>
</div>
<div align='center' id='body'>
    <div id='meta'>
         <h1 class='tex2jax_process'>{titel}</h1>
         <h2>by: {author}</h2>
         <div id='abstract' class='tex2jax_process'>
             <h2 class='abstract'>Abstract:</h2> {abstract} 
         </div>
         <div>
          <div class='references'>
              <h2>Cited by ({citation_count})</h2>
              {citations}
         </div>
         <div class='references'>
              <h2>References ({reference_count})</h2>
              {references}
         </div>
         <div>

    </div>
</div>
</body>
'''


analytics = '''
<script type="text/javascript">

  var _gaq = _gaq || [];
  _gaq.push(['_setAccount', 'UA-29989314-4']);
  _gaq.push(['_trackPageview']);

  (function() {
    var ga = document.createElement('script'); ga.type = 'text/javascript'; ga.async = true;
    ga.src = ('https:' == document.location.protocol ? 'https://ssl' : 'http://www') + '.google-analytics.com/ga.js';
    var s = document.getElementsByTagName('script')[0]; s.parentNode.insertBefore(ga, s);
  })();

</script>'''



if __name__ == '__main__':
    main()

