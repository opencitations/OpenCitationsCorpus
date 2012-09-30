from os import curdir, sep
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import sqlite3 as lite
from unicodedata import normalize

meta_db = "web_demo.db"

import ipdb
BREAK=ipdb.set_trace

def get_meta_dict(arxiv_id):
    con = lite.connect(meta_db)

    with con:
        cur = con.cursor()
        cur.execute("SELECT * FROM meta WHERE arxiv_id = '%s'" % arxiv_id)
        row = cur.fetchone()
        if row is None: return {}
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


def get_html(path):
    if path.endswith('.ico'): return ''
    RW_ID = path.split('/')[-1]
    
    RW_ID=RW_ID.replace('_','/')


    meta = get_meta_dict(RW_ID)
    if meta == {}: return 'Not Found'

    refs = get_references(RW_ID)
    cits = get_citations(RW_ID)


    ref_string = '\n'.join(['<ul>', 
                            '\n'.join(
                ['<li> <a href="%s"> %s </a>' % (x,x) for x in refs]
                ),
                           '</ul>'])
    cite_string = '\n'.join(['<ul>',
                           '\n'.join(['<li> <a href="%s"> %s </a>' % (x,x) for x in cits]),
                           '</ul>'])


    html = """
<div align='center' padding='20px'>
<div style='width:50%; margin-top:50px' align='center'>
           <h1>Related-Work.net</h1>
           <h3> arXiv:{node_id} <h3>
           <h2>{titel}</h2>
           <h3>by: {author}</h3>
<div align='left'>
           <b>Abstract:</b> {abstract} 
</div>
<div width='600px' align='center'>
<div style='float: left; width:300px;' align='left'>
           <h2>References</h2>
           {ref_string}
</div>
<div style='float:left; width:300px' align='left'>
           <h2>Cited by</h2>
           {cite_string}
</div>
</div>
</div>           
</div>
          """.format(node_id = RW_ID, 
                     titel=meta['title'], 
                     author = meta['authors'], 
                     abstract=meta['abstract'],
                     ref_string=ref_string,
                     cite_string=cite_string)

    return html


def to_ascii(string):
    try:
        out= normalize('NFKD', string).encode('ascii','ignore')
    except TypeError:
        out= string
    return out
    



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
        server = HTTPServer(('', 8000), MyHandler)
        print 'Welcome to the machine...'
        server.serve_forever()
    except KeyboardInterrupt:
        print '^C received, shutting down server'
        server.socket.close()



if __name__ == '__main__':
    main()

