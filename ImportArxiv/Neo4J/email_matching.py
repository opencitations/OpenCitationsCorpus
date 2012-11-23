# Aim: Mapp email addresses to authors as possible
# Output: 
# * author node network in format:
#   email-address | Matched names, comma separated | ids of authored papers, comma separated
#   e.g.
#   derhein@gmail.com|Heinrich Hartmann, H. Hartmann, H Hartmann|1209:1341, 1244:1241, math.ag/12041
#   ""|Mr. Noemail|1923:12412

# Intermediate steps:
# * address by paper index:
#   address_of['arxiv_id'] = ['email1','email2']
# * paper by email index 
#   mapping addresses to list of papers:
#   papers_mentioning['email_address'] = ['arxiv_id','arxiv_id']
# * get author names for paper
#   authors_of['arxiv_id'] = [author names]
# * Calculate matchings scores:
#   score['email']['author'] = number of papers by author mentioning email

EMAIL_FILE = '../DATA/ALL_MAIL.txt'
META_DIR = '../DATA/META/JSON/'


import nltk

import sys
sys.path.append('../MetaImport')
from MetaRead import get_json_from_dir

from copy import deepcopy

import ipdb
BREAK = ipdb.set_trace

from pprint import pprint as PRINT

from collections import defaultdict

import json
import pickle, os, sys
# global variables

#sys.path.append('../tools/')
#from shared import to_ascii

ids_by_mail = defaultdict(set)
mails_by_id = defaultdict(set)
match = defaultdict(set)

def main():
    set_author_dict()
    set_email_indices()

    # match['email'] = [authors]
    old_n_match = len(match)
    while True:
        match_single_authors()

        new_matches = len(match) - old_n_match
        old_n_match = len(match)

        if new_matches == 0: break

        print '--\nMatched', new_matches, 'new email addresses to author names. Total:', len(match),'\n'
        remove_matches_from_indices()

def direct_email_match():
    for paper, mails in mails_by_id.items():
        for mail in deepcopy(mails):
            authors = authors_by_id[paper]
            if len(authors) < 2: continue

            # truncated mail address at @ symbol
            mail_name = mail[:mail.find("@")].lower()
            print u"Matching {0} against {1}".format(mail_name, authors)

            distances = sorted([ (author,sum([d_str(mail_name, token) for token in author.lower().split(", ")])) for author in authors ], key=lambda x:x[1])

            print distances
            best_author, best_score = distances[0]
            sec_author, sec_score = distances[1]

            if 1.5*best_score < sec_score:
                print "matched", best_author
                set_match(mail,best_author, paper)

#            raw_input()

def match_single_authors():
    global match
    for paper, authors in authors_by_id.items():
        if not len(authors) == 1: continue

        # single entry of authors
        author = list(authors)[0]
        
        for mail in mails_by_id[paper]:
            print "Matched", mail, "to", author
            set_match(mail,author,paper)


VERBOSE = 0
def remove_matches_from_indices(match = match):
    global authors_by_id, mails_by_id

    for mail, aliases in match.items():
        if VERBOSE: print """
---- {mail:^20} ----
Aliase: {aliases} 
Papers: {0}""".format(ids_by_mail[mail],**locals())

        for paper in deepcopy(ids_by_mail[mail]):
            # author = possible name of mail holder

            #for pauthor in authors_by_id[paper]:
            #    print "edit distance: {0} <-> {1} is {2}".format(pauthor.lower(), author.lower(), d_str(pauthor.lower(),author.lower()))
            #    print 'ratio:', float(d_str(pauthor.lower(),author.lower()))/(len(author)+len(pauthor))

            pauthors = authors_by_id[paper]
            name_matches = set.intersection(aliases,pauthors)
            if VERBOSE: print """* Checking paper {paper:<10}  
   Authors: {pauthors}""".format(**locals())

            if len(pauthors) == 0: 
                if VERBOSE: print "  No author found: Skip"
                continue

            if len(name_matches) > 0:
                # Have an exact match
                if VERBOSE: print '  * Found exact match: {name_matches}'.format(**locals())
                for name in name_matches:
                    set_match(mail,name,paper)
                continue

            if VERBOSE: print "  * No exact match found"         

            if len(pauthors) == 1: 
                if VERBOSE: print "  One paper author left! This should not happen!"
                continue

#            for pauthor in pauthors:
#                print "  * checking author", pauthor, "against", aliases
#                print "    min_d:", min([ d_str(pauthor,alias) for alias in aliases])
#                print "    min_r:", min([ r_str(pauthor,alias) for alias in aliases])
                
            score_list = sorted(
                [
                    # list paper author, and minimal edit distance to alias
                    (pauthor,min([ d_str(pauthor,alias) for alias in aliases])) 
                    # to all paper authors
                    for pauthor in pauthors
                    ],      
                # sort by edit distance
                key = lambda x:x[1]
                )

            if VERBOSE: PRINT(score_list)

            best_author, best_score = score_list[0]
            second_author, second_score = score_list[1]

            if second_score > 2*best_score:
                if VERBOSE: print "   * Matched", best_author
                set_match(mail, best_author, paper)
                aliases.add(best_author)
                match[mail].add(best_author)


d_str = lambda a,b: nltk.metrics.distance.edit_distance(a.lower(),b.lower())
r_str = lambda a,b: float(d_str(a,b))/max(len(a),len(b))


def set_match(mail, name, paper):
    print "Removing", name, mail, "from", paper
    global authors_by_id, mails_by_id, ids_by_mail, match

    # set match entry
    match[mail].add(name)
    try:
        # remove name matches from paper authors
        authors_by_id[paper].remove(name)
    except KeyError: pass
    try:
        # remove email from paper
        mails_by_id[paper].remove(mail)
    except KeyError: pass
    try:
        # remove email from paper reversel lookup
        ids_by_mail[mail].remove(paper)
    except KeyError: pass


def set_email_indices():
    global ids_by_mail, mails_by_id

    fh = open(EMAIL_FILE)
    
    for line in fh:
        entries = line.split('|')
        paper_id = entries[0]
        addresses = filter(
            # drop empty entries, happens if no email is supplied
            None,
            map(str.strip,  # strip off \n
                entries[1:]
                )
            )
        
        for ad in addresses:
            ids_by_mail[ad].add(paper_id)

        mails_by_id[paper_id].update(addresses)

def set_author_dict(limit = -1, cache_file = '../DATA/py_author_cache.pkl'):
    global authors_by_id

    if os.path.exists(cache_file):
        print "Reading from cache"
        with open(cache_file) as cf:
            authors_by_id = pickle.load(cf)
        return

    # if cache file not present:
    authors_by_id = defaultdict(set)
    # calculate author dict
    for rec_id,meta_dict in get_json_from_dir(META_DIR, limit = limit):
        authors_by_id[rec_id].update(meta_dict['creator'])

    # cache author dict
    with open(cache_file,'w') as cf:
        pickle.dump(authors_by_id,cf)

if __name__ == '__main__':
    main()


# hands on cache decorator
def cache(function):
    cache_file = '/tmp/py-cache'
    def wrapped(*args,**kwargs):
        if os.path.exists(cache_file):
            print "Reading authors from cache"
            with open(cache_file) as cf:
                return pickle.load(cf)
        else:
            values = function(*args,**kwargs)
            with open(cache_file,'w') as cf:
                pickle.dump(values,cf)
            return values

    return wrapped
