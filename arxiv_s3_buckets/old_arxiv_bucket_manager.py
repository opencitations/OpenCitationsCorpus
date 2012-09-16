 #!/usr/bin/python

DEBUG = 1

import os, re, gzip, tarfile, pickle, argparse
from subprocess import call


def tar_tex_members(tar):
    for member in tar.getmembers():
        if re.search('tex$',member.name) and member.isreg(): 
            # Test if filename ends with tex or bib, and is a regular file (not a directory)
            yield member

def extract_text_files(bucket_dir):
    # filter file names
    file_names = os.listdir(bucket_dir)

    refhash = {}

    for fn in file_names:
        print 'processing ', fn
        # Example filename: '1201.0654.gz'

        refs = []

        m = re.match('(\d{4})\.(\d{4})\.(.+)',fn)
        if m == None: continue

        arxiv_id   = fn[0:9]
        paper_nr   = int(m.group(2))
        filetype   = m.group(3)
        full_path  = bucket_dir + fn
        
        
        if filetype == 'txt':
            refs = get_refs_txt(full_path)
        elif filetype == 'gz':
            refs = get_refs_tar_gz(full_path)
        elif filetype == 'pdf':
            out_path = full_path[0:-3] + 'txt'
            if os.path.exists(out_path):
                if DEBUG: print 'txt version already existent.'
                continue
            call(['pdftotext', full_path, out_path])
            refs = get_refs_txt(out_path)

        if DEBUG: print refs

        # Write reference list ot hash
        if refs and refhash.has_key(arxiv_id):
            refhash[arxiv_id] = uniquify(refs + refhash[arxiv_id])
        elif refs:
            refhash[arxiv_id] = uniquify(refs)
            
    return refhash

def get_refs_txt(full_path):
    fh = open(full_path, 'rb')
    fulltext = fh.read()
    fh.close()
#    print 'sample:' fulltext[100:150]

    return parse(fulltext)
    

def get_refs_gzip(full_path):
    fh = gzip.open(full_path,'rb')
    refs = parse(fh.read())
    fh.close()
    return refs

def get_refs_tar_gz(full_path):
    refs = []
    try:
        tar = tarfile.open(full_path,'r')
    except:
        if DEBUG: print 'tar opening failed. Trying gzip.'
        try:
            refs = get_refs_gzip(full_path)
        except:
            if DEBUG: print 'gzip opening failed, too. Skipping file.'
        return refs

    for member in tar_tex_members(tar):
        if DEBUG: print '  subfile:', member.name
        text = tar.extractfile(member).read()
        refs += parse(text)
    tar.close()

    return uniquify(refs)


arx_simple = re.compile('(\d{4}\.\d{4})')
arx_tag = re.compile('arXiv:(\d{4}.\d{4})', re.IGNORECASE)
arx_url = re.compile(r'''arXiv.org/
                         (abs|pdf)/          # Match abstracts or pdfs
                         ([a-z\-]{0,5}/)?    # optional parameter hep-th
                         (\d{4}.\d{4})''', re.VERBOSE | re.IGNORECASE)

def parse(tex_string):
    # Find reference section
    # Kill commented line

    # parse arXiv:1112.6310
    # matches = re.finditer('arXiv:(\d{4}.\d{4})',tex_string)
    
    matches = [m.group(1) for m in arx_simple.finditer(tex_string)]
#    matches = [m.group(1) for m in arx_tag.finditer(tex_string)]
#    matches += [m.group(3) for m in arx_url.finditer(tex_string)]

    return matches


def uniquify(seq):
    seen = set()
    seen_add = seen.add
    return [ x for x in seq if x not in seen and not seen_add(x)]


cur_dir = os.getcwd()
data_dir = '/home/web/Desktop/share/buckets/'
bucket_dir = data_dir + '1001/'

reha = extract_text_files(bucket_dir)

fh = open(bucket_dir + 'reference_hash.pkl','wb')
pickle.dump(reha,fh)
fh.close()
