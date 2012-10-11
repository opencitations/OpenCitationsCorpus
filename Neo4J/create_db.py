#
## Writes arxiv meta data and references into a Neo4J graph db.
#
#    by Heinrich Hartmann, www.related-work.net, 2012
#
#
#
### DB Structure diagram:
#                           
#    PAPER <---[type]------ P1  <--[ref]-->  P2 
#                            |               |
#                            |[author]       |[author]
#                            v               v
#    AUTHOR <--[type]------ A1              A2
#
### Description:
#
# *   Paper nodes, with properties:
#     *   title
#     *   abstract
#     *   date         (YYYY-MM-DD, or YYYY, YYYY-MM  if data not available)
#     *   source_url   (e.g. 'http://arxiv.org/abs/1001.1032' )
#     *   source_id    (e.g. 'arxiv:1001.1032')
#     *   unknown_references
#     *   arxiv_meta_dict
#         as a list of unicode strings (see remark below):
#         [ k1, v1 , k2, v2, ... ]
#         vi are lists of meta_dict values joined with separator "|".
#         An example dict is attached at the end of the file.
#
# *   Reference relation: P1 ---> P2,  where P1,P2 are paper nodes. Properties:
#     *   ref_string (e.g. 'Knuth, D., A remark on ... ')
#
# *   Author nodes, with properties:
#     *   name       (e.g. 'Knuth, Daniel-William')
#
# *   Author relation: P ---> A, 
#     where P in (Paper nodes) and A in (Author nodes)
#
# *   Meta nodes: 
#     - PAPER
#     - AUTHOR
#
### Paradigm:
#
# *   Keep the relation structure simple: Do not include relations, that can be 
#     conveniently covered by an index/lookup table. How would we use this 
#     traversal? It is always easy to add relations later on.
# *   Do not throw away information.
#
### Install guide:
#
# *   sudo apt-get install python-jpype
# *   git clone https://github.com/neo4j/python-embedded.git 
# *   sudo python setup.py install
# *   edit .bash.rc:   
#     export CLASSPATH=/usr/lib/jvm/java-6-openjdk/jre/lib/
#     export JAVA_HOME=/usr/lib/jvm/java-6-openjdk/jre/
#
### Remark:
#
# *   We use the embeded-python neo4j library. 
#     As it turns out there are severe speed issues! 
#     [https://github.com/neo4j/python-embedded/issues/15!]
# *   Propertis of Nodes and Relations can be:
#     strings (unicode/ascii), integers, bools
#     and lists of such. Dictionaries are not supported.
#
### Install guide:
#
# *   sudo apt-get install python-jpype
# *   git clone https://github.com/neo4j/python-embedded.git 
# *   sudo python setup.py install
# *   edit .bash.rc:   
#     export CLASSPATH=/usr/lib/jvm/java-6-openjdk/jre/lib/
#     export JAVA_HOME=/usr/lib/jvm/java-6-openjdk/jre/
#
### References:
# *   [Neo4J docs](http://docs.neo4j.org/chunked/milestone/python-embedded.html)
# *   [Github repositoty](https://github.com/neo4j/python-embedded)
# 
### Open Questions:
#
# *   How to deal with unmatched references? 
#     1.  Store them in paper_nodes?
#            a. Store all references in paper_nodes 
#               (redundant, since we want ref relation)
#            b. Store matched references in relations 
#               and unmatched ones in paper_node      
#               (approach taken. Drawback: not very coherent)
#     2.   Store them in a relation to a 'unknown_paper' node. (slow?!)
#     3.   Add a new paper_node and a relation. (slow? data overload?)
#
### Todo: 
#
# *   Coauthor relation
# *   Timing decorators


import os
os.environ['NEO4J_PYTHON_JVMARGS'] = '-Xms512M -Xmx1024M'
#os.environ['CLASSPATH'] = 'usr/lib/jvm/java-6-openjdk/jre/lib/'
#os.environ['JAVA_HOME'] = 'usr/lib/jvm/java-6-openjdk/jre/'

from neo4j import GraphDatabase, INCOMING, Evaluation
import sys
sys.path.append('../MetaImport')
from MetaRead import get_meta_from_pkl
sys.path.append('../tools')
from shared import group_generator

import ipdb as pdb
BREAK = pdb.set_trace

from time import time

DEBUG = 1
db    = GraphDatabase('db_folder')
ROOT = None


def main():

#    import os
#    meta_fill_db(limit = -1)
#    reference_fill_db()
#    write_caches()
#    write_cite_rank()
#    db.shutdown()
    pass
    
def setup_db(db=db):
    global ROOT, PAPER, AUTHOR
    global author_idx, source_idx, label_idx

    if "DEBUG": print "Creating Database."
    # Create a database model - run only once


    # All write operations happen in a transaction
    with db.transaction:
        # create indices to look up arxiv_ids, author names, and node labels
        source_idx = db.node.indexes.create('source_idx')
        author_idx = db.node.indexes.create('author_idx')
        label_idx  = db.node.indexes.create('label_idx')

        # Create nodes
        ROOT = db.reference_node
        ROOT['label'] = 'ROOT'
        PAPER  = db.node(label = 'PAPER')
        AUTHOR = db.node(label = 'AUTHOR')

        # index nodes by label
        label_idx['label']['PAPER']  = PAPER
        label_idx['label']['AUTHOR'] = AUTHOR

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


def meta_fill_db(db=db,limit = -1):
    #
    # Create Paper Nodes
    # 
    start = time()
    for batch_count, batch in enumerate(group_generator(get_meta_from_pkl('../MetaImport/metadata_pkl/', limit = limit),1000)):
        print 'Processing metadata batch %d. Time elapsed: %d sec.' % (batch_count, time() - start)
        with db.transaction:
            for rec_id, meta_dict in batch:
                # create a new node
                paper_node = db.node(
                    label           = 'paper_node arxiv:'+rec_id,
                    title           = meta_dict['title'][0],
                    abstract        = meta_dict['description'][0],
                    unknown_references = [''],
                    date            = meta_dict['date'][0],
                    source_url      = meta_dict['identifier'][0], # Check if really works?
                    source_id       = 'arxiv:'+rec_id,
                    arxiv_meta_dict = [ x for k,v in meta_dict.items() for x in (k, "|".join(v)) ],
                    )

                # add a relation paper_node --[type]--> PAPER
                paper_node.type(PAPER)

                # register in source_id index
                source_idx['id'][paper_node['source_id']] = paper_node

                for author_name in meta_dict['creator']:
                    # create an author name node
                    author_node = add_get_author(author_name)
                
                    # create a relation paper_node --[author]--> author_node
                    paper_node.author(author_node)
            print 'closing transaction'


def add_get_author(author_name):
    '''
    Lookup author name in author_idx.
    If a matching node exists this node is returned.
    Else a new node is created, registered in the index and returned.        
    '''
    # Needs to be inside a db transaction

    # check for existence
    for node in author_idx['name'][author_name]:
        break
    else:
        # Adding the node, create type relation to AUTHOR node, update index
        node = db.node(name=author_name, label='author_node ' + author_name)
        node.type(AUTHOR)
        author_idx['name'][author_name] = node
    
    return node


def reference_fill_db(match_file = '../DATA/ALL_MATCHES.txt' , db=db):
    """
    Reads references from match_file and creates corresponding links in db
    """
   
    in_iter = open(match_file)
    # line format examples at the end of the file

    start = time()
    rel_count = 0
    for batch_count, batch in enumerate(group_generator(in_iter,10000)):
        sys.stderr.write('Processing reference %d x 10000. Elapsed time %d sec. Relations created %d. \n' % (batch_count, time() - start, rel_count))
        with db.transaction:
            for line in batch:
                try:
                    source_id, ref_string, target_id = line.rstrip().split('|')
                except ValueError:
                    print 'Skipped line: not not enough separators "|". ',  line[:20]
                    continue

                # .single property is broken! Have to loop through results (which should be a single one)
                for source_node in source_idx['id']['arxiv:' + source_id]: 
                    break
                else: 
                    print "Skipped line: source id not forund. ", line[:20]
                    continue
                

                if not target_id == '':
                    # Lookup target_id in the index
                    target_node = None
                    for target_node in source_idx['id']['arxiv:' + target_id]: 
                        break

                    if target_node:
                        # create reference relation
                        source_node.ref(target_node, ref_string=ref_string, label='Reference')
                        rel_count += 1
                        continue

                # Found nothing?
                # .append is not working!
                # source_node['unknown_references'] += [ref_string]


def unmatched_reference_fill_db(match_file = '../DATA/ALL_MATCHES.txt' , db=db):
    """
    Findes lines in match_file, where the target cannot be found, and adds
    the corresponding reference strings to 'unknown_references' list in the source.
    """
   
    in_iter = open(match_file)
    # line format examples at the end of the file

    start = time()
    rel_count = 0
    last_id = ''
    ref_buffer = []
    for batch_count, batch in enumerate(group_generator(in_iter,10000)):
        sys.stderr.write('Processing reference %d x 10000. Elapsed time %d sec. Relations created %d. \n' % (batch_count, time() - start, rel_count))
        with db.transaction:
            for line in batch:
                try:
                    source_id, ref_string, target_id = line.rstrip().split('|')
                except ValueError:
                    print 'Skipped line: not not enough separators "|". ',  line[:20]
                    continue

                if not target_id == '':
                    # Lookup target_id in the index
                    target_node = None
                    for target_node in source_idx['id']['arxiv:' + target_id]: 
                        break
                    if target_node:
                        # skip if target exists
                        last_id = source_id
                        continue

                # target node does not exist here #

                if source_id == last_id: # on same node?
                    ref_buffer.append(ref_string)
                    continue

                # new source_id #

                # lookup source node 
                for last_node in source_idx['id']['arxiv:' + last_id]:
                    break
                else: 
                    print "Skipped line: source id not forund. ", last_id
                    last_id = source_id
                    continue
                # last node exists #

                # write old references to last node
                last_node['unknown_references'] += ref_buffer                
                last_id = source_id
                ref_buffer = [ref_string]


def write_caches():
    start = time()
    for i, batch in enumerate(group_generator(PAPER.type.incoming, 1000)):
        print "Filling citaion and author buffers. %d papers processed in %d sec." % (i*1000, time()-start)
        with db.transaction:
            for paper_rel in batch:
                paper_node = paper_rel.startNode

                ref_count = 0
                for ref in paper_node.ref.outgoing:
                    ref_count += 1 

                cite_count = 0
                for ref in paper_node.ref.incoming:
                    cite_count += 1 

                paper_node['c_reference_count'] = ref_count
                paper_node['c_citation_count'] = cite_count
                paper_node['c_authors'] = ' and '.join([ a_rel.endNode['name'] for a_rel in paper_node.author ])

def write_cite_rank(iterations=4):
    start = time()
    # damping factor
    d = 0.85 
    # initial value
    cr_0 = 1.

    for iteration in range(iterations):
        for batch_count, batch in enumerate(group_generator(PAPER.type.incoming, 1000)):
            print "Calculating CiteRank. Iteration %d. Processed %d papers in %d sec." % (iteration, batch_count*1000, time()-start)
            with db.transaction:
                for paper_rel in batch:
                    paper_node = paper_rel.startNode
                    
                    cr = (1 - d)
                    for cite_rel in paper_node.ref.incoming:
                        cite_node = cite_rel.startNode
                        try:
                            cr_node = cite_node['c_cite_rank']
                        except KeyError:
                            cr_node = cr_0                            
                        cr += d * cr_node / cite_node['c_reference_count']

                    paper_node['c_cite_rank'] = cr


def build_search_index():
    start = time()
    try:
        search_idx = db.nodes.indexes.get('search_idx')
#        with db.transaction:
#            search_idx.delete()
    except ValueError:
        pass
    
#    search_idx = db.nodes.indexes.create('search_idx',type='fulltext')

    # Loop through papers
    for batch_count, batch in enumerate(group_generator(PAPER.type.incoming, 1000)):
        print "Building search index. Processing paper %d. Elapsed time %d sec," % ( batch_count*1000, time()-start)
        with db.transaction:
            for paper_rel in batch:
                paper_node = paper_rel.startNode
                search_idx['title'][paper_node['title']]=paper_node

    for batch_count, batch in enumerate(group_generator(AUTHOR.type.incoming, 1000)):
        print "Building search index. Processing paper %d. Elapsed time %d sec," % ( batch_count*1000, time()-start)
        with db.transaction:
            for author_rel in batch:
                author_node = author_rel.startNode
                name  = author_node['name'].replace(',',' ')
                search_idx['author'][name]=author_node


if __name__ == '__main__':

    try:
        if not db.node.indexes.exists('author_idx'):
            setup_db()
        else:
            init_globals()

        main()

    except:
        import sys, traceback
        type, value, tb = sys.exc_info()
        traceback.print_exc()
        pdb.post_mortem(tb)


#
# Example arxiv_meta dict:
#
# {
# 'contributor'        : [],
# 'coverage'           : [],
# 'creator'            : [u'Pala, Marco G.', u'Governale, Michele', u'K\xf6nig, J\xfcrgen'],
# 'date'               : [u'2007-04-02', u'2007-08-29'],
# 'description'        : [u'  We present...gate or bias voltages.\n', u'Comment: 11 pages, 4 figures'],
# 'format'             : [],
# 'identifier'         : [u'http://arxiv.org/abs/0704.0204', u'New J. Phys. 9 (2007) 278', u'doi :10.1088/1367-2630/9/8/278'],
# 'language'           : [],
# 'publisher'          : [],
# 'relation'           : [],
# 'rights'             : [],
# 'source'             : [],
# 'subject'            : [u'Condensed Matter - Superconductivity', u'Condensed Matter - Mesoscale and Nanoscale Physics'],
# 'title'              : [u'Non-Equilibrium Josephson and Andreev Current through Interacting\n  Quantum Dots'],
# 'type'               : [u'text']
# }


#
# Example ALL_MATCHES.txt lines:
#
#0707.1231|Jarvis, P. D. and Morgan,  .... . Phys. Lett. , 19: 501-- , , 2006.|math-ph/0508041
#hep-th/0412066|J. Giedt, Nucl. Phys ... 232.|hep-th/0301232
#math-ph/9912009|P. Bizo n, ph Equivariant ... 3-sphere , math-ph/9910026.|math/9910026
#1204.1075|Vasiliy Dolgushev, ... :0807.5117 (2008).|0807.5117
