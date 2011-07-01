import os, sys

from parse_xml import run as parse_xml
from sanitize import run as sanitize
from unify_identifiers import run as unify_identifiers
from merge_sort import run as merge_sort
from load_solr import run as load_solr
from merge_solr import run as merge_solr
from combine_articles import run as combine_articles
from map_identifiers import run as map_identifiers

def run_all(input_directory, output_directory):
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    def rel(filename):
        return os.path.join(output_directory, filename)

    #parse_xml(input_directory, rel('articles-raw.csv'), rel('citations-raw.csv'))
    #sanitize(rel('articles-raw.csv'), rel('articles-sanitized.csv'))
    unify_identifiers(rel('articles-sanitized.csv'), rel('articles-id-unified.csv'))
    merge_sort(rel('articles-id-unified.csv'), rel('articles-id-unified-sorted.csv'))
    return
    load_solr(rel('articles-id-unified-sorted.csv'))
    merge_solr(rel('articles-id-unified-sorted.csv'), rel('articles-solr-unified.csv'))
    merge_sort(rel('articles-solr-unified.csv'), rel('articles-solr-unified-sorted.csv'))
    combine_articles(rel('articles-solr-unified-sorted.csv'), rel('articles-tidy.csv'), rel('id-mapping.csv'))
    combine_articles(rel('articles-id-unified-sorted.csv'), rel('articles-tidy.csv'), rel('id-mapping.csv'))
    map_identifiers(rel('citations-raw.csv'), rel('citations-tidy.csv'), rel('id-mapping.csv'))


if __name__ == '__main__':
    run_all(*sys.argv[1:3])
