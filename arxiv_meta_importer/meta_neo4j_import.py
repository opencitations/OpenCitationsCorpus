# Loads records from pickle file and inserts them into Neo4J database
# using neo4j python package

from neo4j import GraphDatabase, INCOMING, Evaluation
import pickle

# db   = GraphDatabase('db_folder')
# ROOT = db.reference_node

def init_globals():
    global db
    global authors, papers, subjects
    global author_idx, paper_idx, subject_idx, date_idx

    authors = ROOT.AUTHORS.single.end
    papers = ROOT.PAPERS.single.end
    subjects = ROOT.SUBJECTS.single.end

    if authors == None: create_db()

    paper_idx =     db.node.indexes.get('papers')
    author_idx =    db.node.indexes.get('authors')
    subject_idx =   db.node.indexes.get('subjects')
    date_idx =      db.node.indexes.get('date') # as ISO8601

def create_db():
    print "Initializing Database."
    # Create a database model - run only once
    global db
    global authors, papers, subjects
    global author_idx, paper_idx, subject_idx, date_idx

    # All write operations happen in a transaction
    with db.transaction:
        # ad a node for the papers and authors type
        papers = db.node()
        authors = db.node()
        subjects = db.node()
 
        # create edges of type PAPERS and AUTHORS connecting the reference_node to the above nodes.
        db.reference_node.PAPERS(papers)
        db.reference_node.AUTHORS(authors)
        db.reference_node.SUBJECTS(subjects)
 
        # indexes, helps us rapidly look up papers and authors
        paper_idx =     db.node.indexes.create('papers')
        author_idx =    db.node.indexes.create('authors')
        subject_idx =   db.node.indexes.create('subjects')
        date_idx =      db.node.indexes.create('date')
    return

def get_records(limit = 10):
    # load our arxiv dump from a file
    import pickle
    f = open('data_2012.pkl','rb')
    recs = pickle.load(f)

    # limit to 10 records by default
    recs = recs[0:limit]
    
    # split recs return a gernator object to loop through the records.
    for rec in recs:
        header, meta, about = rec
        yield meta.getMap()

def add_get_author(a_name):
    # check for existence
    author = author_idx['name'][a_name].single
    if author == None:
        # Adding the node, update index
        print 'adding author', a_name
        author = db.node(name=a_name)
        author.INSTANCE_OF(authors)
        author_idx['name'][a_name]=author
    else:
        print 'skipping author', a_name
    return author

def add_get_subject(s_name):
    subject = subject_idx['name'][s_name].single
    if subject == None:
        print 'adding subject', s_name
        subject = db.node(name=s_name)
        subject.INSTANCE_OF(subjects)
        subject_idx['name'][s_name] = subject
    else:
        print 'skipping subject', s_name
    return subject

def paper_is_new(pdata):
    # test for title only. Need a better test later.
    paper = paper_idx['title'][pdata['title']].single
    return paper == None

def encode_record(rec):
    # transform unicode entries to ascii the brutal way.
    if type(rec) == unicode:
        rec = rec.encode('ascii','ignore')
    elif type(rec) == list:
        rec = [encode_record(i) for i in rec]            
    elif type(rec) == dict:
        for (k,v) in rec.items():
            rec[k]=encode_record(v)

    if type(rec) == str:
        rec = rec.replace('\\','')
        rec = rec.replace('\n','')
        rec = rec.replace('\'','')
        rec = rec.replace('\"','')

    return rec

def add_papers(records):
    with db.transaction:
        for meta in records:
            pdata = {
                     'title':    meta['title'][0],
                     'abstract': meta['description'][0],
                     'date':     meta['date'][-1],          # most recent date
                     'url':      meta['identifier'][0],     # url
                     }

            if not paper_is_new(pdata):  
                print 'skipping paper ', pdata['title']
                continue

            print 'adding paper ',pdata['title']
            
            # add paper to the db
            paper = db.node()
            for k,v in pdata.items(): paper.setProperty(k,v)
            # Include a copy of the raw data for later use.
            paper.setProperty('raw',pickle.dumps(encode_record(meta), 0))
            
            paper.INSTANCE_OF(papers)
            paper_idx['title'][pdata['title']] = paper
            date_idx['date'][pdata['date']] = paper
 
            # link to author
            for a_name in meta['creator']:
                author = add_get_author(a_name)
                author.WROTE(paper)
                
            # link to subject
            for s_name in meta['subject']:
                subject = add_get_subject(s_name)
                paper.SUBJECT(subject)
    return


def get_meta_json(limit = 10):
    import json
    for meta in get_records(limit):
        meta = encode_record(meta)

        pdata = {
            'authors':  meta['creator'],          # List of Authors
            'title':    meta['title'][0],
#            'abstract': meta['description'][0],    # Abstract
            'date':     meta['date'][-1],          # most recent date
            'url':      meta['identifier'][0],     # url
            'subject':  meta['subject']
            }

        yield json.dumps(pdata)

def write_meta_json(limit = 10, filename = 'meta_json.txt'):
    fh = open(filename,'w')
    for line in get_meta_json(limit):
        fh.write(line + '\n')
    fh.close()

# create_db()

# adds the first 10 papers in the record
# add_papers(get_records())

# db.shutdown()

