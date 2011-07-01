from __future__ import division
import itertools, csv, random
from collections import defaultdict

import matplotlib.pyplot as plt
import matplotlib.colors
import networkx as nx

from model import Article
from recluster import recluster
from unify_identifiers import IDENTIFIERS

def count(xs):
    v = defaultdict(int)
    for x in xs:
        if x:
            v[x] += 1
    return sorted(v.iteritems(), key=lambda x:x[1])

COLORS = """#ff0000 #00ff00 #0000ff #ffff00 #ff00ff #00ffff #500000 #005000
            #000050 #505000 #500050 #005050 #000000 #505050 #A00000 #00A000
            #0000A0 #A0A000 #A000A0 #00A0A0 #A0A0A0""".split()

for i in range(10000):
    COLORS.append('#'+''.join('%02x' % random.randint(0, 255) for i in range(3)))

split_count = 0

def split(groups):
    global split_count
    g = nx.Graph()
    weights = {'pmc_oa': 4, 'pmc_oa_reference': 1, 'pubmed_api': 4, 'pmc_oa_retraction': 3}
    identifiers = set()

    for i, group in enumerate(groups):
        for article in group:
            weight = weights[article.provenance]
            article_node_id = 'document:%s' % article.id
            g.add_node(article_node_id, type='document', document=article, group=i)

            for identifier in IDENTIFIERS:
                value = getattr(article, identifier)
                identifier_node_id = 'identifier:%s:%s' % (identifier, value)
                if not value:
                    continue
                g.add_node(identifier_node_id, type='identifier', scheme=identifier, value=value, group=None)
                g.add_edge(article_node_id, identifier_node_id, weight=weight)
                identifiers.add(identifier_node_id)

    plt.clf()
    pos = nx.spring_layout(g, iterations=200)
    for n in pos:
        grp = g.node[n]['group']
        c = 'w' if grp is None else COLORS[grp]
        s = 'o' if grp is not None else 's^dph8'[IDENTIFIERS.index(g.node[n]['scheme'])]
        nx.draw_networkx_nodes(g, pos, [n], node_color=c, node_shape=s)
    nx.draw_networkx_edges(g, pos, alpha=0.8)
    labels = dict((n, n.split(':', 1)[1]) for n in pos)
    nx.draw_networkx_labels(g, pos, labels, font_size=8)
    plt.axis('off')
    plt.savefig("/home/alex/reclusterings/%08i.png" % split_count)
    split_count += 1
#    plt.show()
    return

    for identifier in identifiers:
        group_ids = [g.node[n]['group'] for n in g[identifier]]
        print "||", identifier.ljust(40), group_ids



def run(input_filename, output_filename):
    reader = itertools.imap(lambda a:Article(*[f.decode('utf-8') for f in a]), csv.reader(open(input_filename, 'r')))
    writer = csv.writer(open(output_filename, 'w'))

    group_counter, split_counter = 0, 0

    for i, (group_id, articles) in enumerate(itertools.groupby(reader, lambda a:a.group)):
        group_id, articles = int(group_id), list(articles)
        if i % 1000 == 0 and i:
            print "%8i %8i %8i %8i %8.5f%%" % (i, group_id, split_counter, group_counter, split_counter/group_counter*100)

        groups = list(recluster(articles))

        groups.sort(key=lambda g:-len(g))
        if len(groups) > 1 or sum(len(g) for g in groups[1:]) > 8:
            split_counter += 1
            print len(groups), sorted(map(len, groups))
#            for identifier in IDENTIFIERS:
#                print "  ", identifier, [count(getattr(a, identifier) for a in g) for g in groups]
            split(groups)


        for group in groups:
            gc = unicode(group_counter)
            for article in group:
                article = article._replace(group = gc)
                writer.writerow([f.encode('utf-8') for f in article])
            group_counter += 1

if __name__ == '__main__':
    run('../parsed/articles-id-unified-sorted.csv', '../parsed/articles-reclustered.csv')
