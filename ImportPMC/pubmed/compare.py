from __future__ import division
import re, itertools

from Levenshtein import distance as levenshtein_distance

def levenshtein(a, b):
    d = levenshtein_distance(a, b) / max(len(a), len(b))
    return (1 - d)

def compare_authors(a, b):
    a_names, b_names = a.replace(u'.', u'').split(u', '), b.replace(u'.', u'').split(u', ')

    cs = []

    for (i, a_name), b_name in zip(enumerate(a_names), b_names):
        a_name, b_name = a_name.split(' '), b_name.split(' ')
        if len(a_name) > len(b_name):
            a_name, b_name = b_name, a_name

        a_name = sorted(itertools.chain(*[(p if p.isupper() else [p]) for p in a_name if p]), key=lambda x:(-len(x), x))
        b_name = sorted(itertools.chain(*[(p if p.isupper() else [p]) for p in b_name if p]), key=lambda x:(-len(x), x))

        for (j, a_part), b_part in itertools.product(enumerate(a_name), b_name):
            if len(a_part) == 1 or len(b_part) == 1:
                # One is an initial
                cs.append(((i, j), (1, 1 if a_part[0] == b_part[0] else 0)))
            else:
                cs.append(((i, j), (1, levenshtein(a_part.lower(), b_part.lower()))))
            #print a_part, b_part, cs[-1]

    cs.sort(key=lambda x:-x[1][1])
    seen = set()
    ds = []
    for c, d in cs:
        if c in seen:
            continue
        seen.add(c)
        ds.append(d)

    #print "DS", ds, a, b, sum(c*d for c,d in ds) / sum(c for c,d in ds)

    try:
        return 0.7, sum(a*b for a,b in ds) / sum(a for a,b in ds)
    except ZeroDivisionError:
        return 0, 0



INTEGER_RE = re.compile('^\d+')
def compare_integer(a, b, weight=1):
    #print "A", type(a), type(b)
    a = INTEGER_RE.match(a)
    b = INTEGER_RE.match(b)
    if a and b:
        a, b = a.group(0), b.group(0)
        # Use Levenshtein as typos appear to occur relatively often
        return (weight, levenshtein(a, b))
    else:
        return (0, 0)

class AttributeDict(dict):
    def __getattr__(self, key):
        return self.get(key)

def compare(a, b, records):
    a, b = map(AttributeDict, (a, b))

    cs = []
    if a.doi and b.doi:
        cs.append((0.2, 1 if a.doi == b.doi else 0))
    if a.pmid and b.pmid:
        cs.append((0.6, 1 if a.pmid == b.pmid else 0))
    if a.pmc and b.pmc:
        cs.append((0.6, 1 if a.pmc == b.pmc else 0))
    if a.uri and b.uri:
        cs.append((0.6, 1 if a.uri == b.uri else 0))
    if a.volume and b.volume:
        cs.append(compare_integer(a.volume, b.volume, weight=0.4))
    if a.issue and b.issue:
        cs.append(compare_integer(a.issue, b.issue, weight=0.4))
    if a.source and b.source:
        cs.append((0.4, levenshtein(a.source.replace('.', '').lower(), b.source.replace('.', '').lower())))
    if a.title and b.title:
        cs.append((1, levenshtein(a.title.lower(), b.title.lower())))
    if a.author and b.author:
        cs.append(compare_authors(a.author, b.author))
    if a.uri and b.uri and a.uri == b.uri:
        cs.append((100, 1))

    if a.year and b.year:
        try:
            if int(a.year) < 1800 or int(b.year) < 1800:
                raise ValueError
            cs.append((0.5, 2** -(abs(int(a.year)-int(b.year)) / 3)))
        except ValueError:
            pass
    try:
        return sum(a for a,b in cs) / sum(a*b for a,b in cs) - 1
    except ZeroDivisionError:
        return float('inf')

