from os import curdir, sep
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from neo4j import GraphDatabase
from unicodedata import normalize

db = GraphDatabase('db_folder')

import ipdb
BREAK=ipdb.set_trace


def init_globals(db=db):
    '''Restore global varibales on a running db'''
    global ROOT, PAPER, AUTHOR
    global author_idx, source_idx, label_idx
    
    label_idx  = db.node.indexes.get('label_idx')
    source_idx = db.node.indexes.get('source_idx')
    author_idx = db.node.indexes.get('author_idx')
    
    AUTHOR = label_idx['label']['AUTHOR'].single
    PAPER  = label_idx['label']['PAPER'].single
    ROOT   = db.reference_node





def get_html(path):
    if path.endswith('.ico'): return ''
    if path.split('/')[-2] == 'author':
        return get_autor_page(path.split('/')[-1])
        
    RW_ID = path.split('/')[-1]
    RW_ID=RW_ID.replace('_','/')

    for paper_node in source_idx['id'][RW_ID]:
        break
    else:
        return "Id %s not found" % RW_ID

    ref_string = '<ul>'
    reference_count = 0
    for ref in paper_node.ref.outgoing:
        reference_count += 1
        sub_paper_node = ref.endNode
        sub_citation_count = 0
        for sub_ref in sub_paper_node.ref.incoming: sub_citation_count += 1
        authors = ' and '.join([ rel.endNode['name'] for rel in sub_paper_node.author ])
        title   = sub_paper_node['title']
        year    = sub_paper_node['date'][0:4]
        entry   = u"{authors}, {title}, {year}".format(**locals())
        href = '/' + sub_paper_node['source_id'].replace('/','_')
        ref_string += to_ascii(u'<li><a href="{href}">({sub_citation_count}) {entry} </a></li> \n'.format(**locals()))

    ref_string += '\n'.join(['<li>' + u_ref_string + '</li>' for u_ref_string in paper_node['unknown_references'][1:]])
    ref_string += '</ul>'

    citation_count = 0
    cite_string = '<ul>'
    for ref in paper_node.ref.incoming:
        citation_count += 1
        sub_paper_node = ref.startNode
        sub_citation_count = 0
        for sub_ref in sub_paper_node.ref.incoming: sub_citation_count += 1
        authors = ' and '.join([ author_rel.endNode['name'] for author_rel in sub_paper_node.author ])
        title   = sub_paper_node['title']
        year    = sub_paper_node['date'][0:4]
        entry   = u"{authors}, {title}, {year}".format(**locals())
        href = '/' + sub_paper_node['source_id'].replace('/','_')
        cite_string += to_ascii(u'<li><a href="{href}">({sub_citation_count}) {entry} </a></li>'.format(**locals()))
    cite_string += '</ul>'



    html = u'''
<body class="tex2jax_ignore">
<div id='headder'>
    <h1 style='display:inline'> <a href='http://related-work.net'>Related-Work.net</a> </h1> 
    <h2 style='display:inline'> 
      >
      <a href='http://arxiv.org'> arXiv </a>  
      >
      <a href='{source_url}'>{short_id}</a>
    </h2>
</div>
<div align='center' id='body'>
    <div id='meta'>
         <h1 class='tex2jax_process'>{titel}</h1>
         <h2>by: {author}</h2>
         <div id='abstract' class='tex2jax_process'>
             <h2>Abstract:</h2> {abstract} 
         </div>
         <div>
          <div style='float:left; width:100%' align='left' class='references'>
              <h2>Cited by ({citation_count})</h2>
              {citations}
         </div>
         <div style='float: left; width:100%;' align='left' class='references'>
              <h2>References ({reference_count})</h2>
              {references}
         </div>
         <div>

    </div>


</div>
</body>
'''.format(
        node_id = RW_ID,
        short_id = RW_ID.split(':')[-1],
        source_url = paper_node['source_url'],
        titel = paper_node['title'],
        abstract = paper_node['abstract'],
        author =  ' and '.join([ '<a href= "%s"> %s </a>' % ("/author/" + author_rel.endNode['name'].replace(" ","_"), author_rel.endNode['name']) for author_rel in paper_node.author ]),
        references = ref_string,
        citations = cite_string,
        citation_count = citation_count,
        reference_count = reference_count
        )

        
    return to_ascii(mathjax + css + html)


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

    paper_string = '<ul>'
    for author_rel in author_node.author.incoming:
        paper_node = author_rel.startNode
        href = '../'+paper_node['source_id'].replace('/','_')
        title = paper_node['title']
        year = paper_node['date'][0:4]
        paper_string += u'<li><a href="{href}"> {title}, {year}</li>'.format(**locals())
    paper_string += '</ul>'
        
    html = u'''
<h1> {author_name} </h1>
<h2> Articles </h2>
{paper_string}
'''.format(author_name = author_name, paper_string = paper_string)

    return to_ascii(html)




class MyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            self.send_response(200)
            self.send_header('Content-type',	'text/html')
            self.end_headers()
            self.wfile.write(get_html(self.path))
        except IOError:
            self.send_error(404,'File Not Found: %s' % self.path)

def main():
    try:
        init_globals()
        server = HTTPServer(('', 8000), MyHandler)
        print 'Welcome to the machine...'
        server.serve_forever()
    except:
        print '^C received, shutting down server'
        db.shutdown()
        server.socket.close()




def get_meta_dict(arxiv_id):
    con = lite.connect(meta_db)

    with con:
        cur = con.cursor()
        cur.execute("SELECT * FROM meta WHERE arxiv_id = '%s'" % arxiv_id)
        row = cur.fetchone()
        if row is None: return {}
        BREAK()
        row = map(to_ascii, row)
        schema = 'rec_id, authors, title, abstract, info, subject, year'.split(', ')
        author_dict = dict(zip(schema,row))
        
    return author_dict


def get_references(arxiv_id):
    con = lite.connect(meta_db)

    with con:
        cur = con.cursor()
        cur.execute("SELECT target_id FROM refs WHERE source_id = '%s'" % arxiv_id)
        references = [x[0].replace('/','_') for x in cur.fetchall()]
    return map(to_ascii,references)


def get_citations(arxiv_id):
    con = lite.connect(meta_db)

    with con:
        cur = con.cursor()
        cur.execute("SELECT source_id FROM refs WHERE target_id = '%s'" % arxiv_id)
        rows = cur.fetchall()
        citations = [x[0].replace('/','_') for x in rows]
    return map(to_ascii, citations)






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

#abstract h2 {
display: inline;
line-height: 100%;
}

a:link { color:#000070; text-decoration:none; }
a:hover { text-decoration:underline; }
a:visited { color:#A00093; text-decoration:none; }


#meta {
   width: 80%;
   margin-top:50px;
   align : center;
}

#headder {
padding: 8px;
border-style: none none dotted none;
border-width: 2px;
background-color: #E9E6EE;
}

.references {
font-family: 'Lucida Grande', helvetica, arial, verdana, sans-serif;
font-size: 90%;
line-height: 130%;
} 

.references ul {
margin: 0;
}
.references ul li {
margin-top: 5;
}

--> 
</style>'''






if __name__ == '__main__':
    main()

