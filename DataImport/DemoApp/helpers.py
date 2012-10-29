from re import findall
from unicodedata import normalize

def get_author_html(paper_node):
    authors = paper_node['c_authors'].split(" and ")
    authors.sort()
    return ' and '.join(
        u'''<a href="{href}"> {name} </a>'''.format(
            href = '/author/'+name.replace(' ','_'),
            name = abbrev_full_name(name))
        for name in authors)

def get_ref_html(node):
    return to_ascii(u'''<a href="{href}">{authors}, <em>{title}</em>, {year} (citations: {citation_count})</a>'''.format(
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
    abbrev_first_name = ' '.join( " " + first_name[0] +'.' for first_name in findall(r"[a-zA-Z]+", rest))
    return sir_name + ' ' + abbrev_first_name

def to_ascii(string):
    try:
        out = normalize('NFKD', string).encode('ascii','xmlcharrefreplace')
    except TypeError:
        out = string
    return out

