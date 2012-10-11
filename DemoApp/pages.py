from itertools import islice, chain
from re import findall, sub
from templates import (front_html, main_template, 
                       author_template, search_template,
                       html_head)

from helpers import get_author_html, get_ref_html, to_ascii


def get_paper_page(paper_node):
    '''Renders paper page from neo4j node'''

    rw_id = paper_node['source_id']
    ref_nodes = ( ref.endNode for ref in paper_node.ref.outgoing )
    ref_list  = ( get_ref_html(node) for node in sorted(ref_nodes, key=lambda node: node['c_citation_count'], reverse = True) )
    ref_list_complete = chain(ref_list, paper_node['unknown_references'][1:])

    ref_string = '<ul>'
    ref_string += '\n'.join( '<li>' + entry + '</li>' for entry in ref_list_complete )
    ref_string += '</ul>'

    cite_nodes = ( ref.startNode for ref in paper_node.ref.incoming )
    cite_list  = ( get_ref_html(node) for node in sorted(cite_nodes, key=lambda node: node['c_citation_count'], reverse = True) )

    cite_string = '<ul>'
    cite_string += '\n'.join( '<li>' + entry + '</li>' for entry in cite_list )
    cite_string += '</ul>'

    html = main_template.format(
        node_id         = rw_id,
        short_id        = rw_id.split(':')[-1],
        source_url      = paper_node['source_url'],
        title           = paper_node['title'],
        abstract        = paper_node['abstract'],
        author          = get_author_html(paper_node),
        references      = ref_string,
        citations       = cite_string,
        citation_count  = paper_node['c_citation_count'],
        reference_count = paper_node['c_reference_count'],
        )
        
    return to_ascii(html_head + html)

def get_search_page(search_string, search_idx, limit = None):
    '''Renders search page from search_string and search index'''
    search_string  = sub('[^\w-]+', ' AND ', search_string)
    author_html = u'<ul>'
    for author_node in islice(search_idx.query('author', search_string),0,limit): 
        author_html += u'''<li> <a href='%s'> %s </a> </li>''' % ("/author/" + author_node['name'].replace(' ','_'), author_node['name'] )
    author_html += '</ul>'
    
    
    results_node = islice(search_idx.query('title', search_string),0,limit)
    results_node_sorted = sorted(results_node, key = lambda node: node['c_citation_count'], reverse=True)
    results_html  = ( '<li>' + get_ref_html(paper_node) + '</li>\n' for paper_node in results_node_sorted)
    
    paper_html = u'<ul>'
    paper_html += u''.join(results_html)
    paper_html += u'</ul>'

    html = search_template.format(
        search_string = search_string,
        authors = author_html,
        articles = paper_html
        )
    
    return to_ascii(html_head + html)

def get_autor_page(author_name, author_idx):
    '''Renders author page from author_name and search index'''

    print 'Get author:', author_name
    author_name = author_name.replace('_',' ')

    for author_node in author_idx['name'][author_name]: break
    else: return "Author %s not found" % to_ascii(author_name)

    paper_nodes = ( ref.startNode for ref in author_node.author.incoming )
    paper_nodes_sorted = sorted(paper_nodes, key=lambda node: node['c_citation_count'], reverse=True)
    papers_html = ( '<li>' + get_ref_html(paper_node) + '</li>\n' for paper_node in paper_nodes_sorted )

    ref_string = u'<ul>'
    ref_string += u''.join( papers_html )
    ref_string += u'</ul>'

    html = author_template.format(
        author_name = author_name,
        author_url  = '#',
        references = ref_string,
        )       

    print 'Get author check'
    return to_ascii(html_head + html)


def get_front_page():
    '''Renders Related-Work front page'''
    return to_ascii(html_head + front_html)
