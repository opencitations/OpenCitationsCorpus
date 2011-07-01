from __future__ import division
from pprint import pprint
from collections import defaultdict
import solr, itertools, csv, re, time, resource, pickle, os
from xml.sax._exceptions import SAXParseException

from model import Article
from recluster import smart_recluster
import mergesort

class SolrMerger(object):
    def __init__(self, input_filename, output_filename):
        self.input_filename, self.output_filename = input_filename, output_filename
        self.cache_directory = os.path.join(os.path.expanduser('~'), '.pubmed', 'solr-merge')
        self.filenames = dict((n, os.path.join(self.cache_directory, n)) for n in ('seen', 'groups'))
        self.load_cache()

    def load_cache(self):
        if all(map(os.path.exists, self.filenames.values())):
            for name in self.filenames:
                setattr(self, name, pickle.load(open(self.filenames[name])))
        else:
            self.groups, self.seen = defaultdict(set), set()

    def save_cache(self):
        if not os.path.exists(self.cache_directory):
            os.makedirs(self.cache_directory)
        for name in self.filenames:
            pickle.dump(getattr(self, name), open(self.filenames[name], 'w'))


    def run(self):
        reader = csv.reader(open(self.input_filename, 'r'))
        reader = (Article(*(f.decode('utf-8') for f in a)) for a in reader)

        s = solr.SolrConnection('http://localhost:8983/solr')

        groups, seen = self.groups, self.seen
        biggest = 0

        started, total = time.time(), time.time()
        for i, (initial_group, articles) in enumerate(itertools.groupby(reader, lambda a:a.group)):
            if i % 100 == 0 and i > 0:
                duration, started = time.time() - started, time.time()
                print "%8d %8d %6.2f %6.4f %6.4f %s" % (i, len(seen), duration, (duration / 100), (time.time() - total) / len(seen), resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)

            initial_group = int(initial_group)
            if initial_group in seen:
                continue

            if i % 50000 == 0:
                print "Saving cache"
                self.save_cache()

            articles = list(articles)
            article_ids = set(a.id for a in articles)
            articles[1:] = []
            article = articles[0]

            query = re.sub(r'\W+', ' ', article.title)

            try:
                for size in itertools.count(3):
                    size = 2**size

                    results = s.query(query, rows=size)

                    for a in results:
                        if a['id'] not in article_ids:
                             del a['score']
                             a['keywords'] = frozenset(a['keywords'])
                             a['author'] = ', '.join(a['author'])
                             articles.append(Article(**a))

                    clusters = smart_recluster(articles)
                    if size >= 256:
                        print "%9d %9d" % (initial_group, size)
                    if len(results) < size or max(len(c) for c in clusters) < size*0.75:
                    #    print "OK", size
                        break
                    #else:
                    #    print "Extending", size
            except solr.core.SolrException, e:
                groups[initial_group] = set([initial_group])
                continue
            except SAXParseException, e:
                groups[initial_group] = set([initial_group])
                continue


            #print '='*120
            #for c in clusters:
            #    for a in c:
            #        print '%9d %s %s' % (int(a.group), a.id[:60].ljust(60), a.title[:110])
            #    print '-'*120

            for cluster in clusters:

                cluster_groups = set(int(a.group) for a in cluster)
                #print cluster_groups
                if initial_group in cluster_groups:
                    seen |= cluster_groups

                group = groups[iter(cluster_groups).next()]
                for cg in cluster_groups:
                    group.add(cg)
                    group |= groups[cg]
                    groups[cg] = group
                    if len(group) > biggest:
                        biggest = len(group)
                #        print biggest

            #print initial_group, [[int(a.group) for a in c] for c in clusters]
            if not any(initial_group in [int(a.group) for a in c] for c in clusters):
                raise RuntimeError

            if initial_group not in groups:
                raise AssertionError

        groups = set(tuple(sorted(group)) for group in groups.values())
        groups = enumerate(sorted(groups))

        new_groups = {}
        for group_id, group_set in groups:
            for group in group_set:
                new_groups[group] = group_id
        groups = new_groups

        reader_f, writer_f = open(self.input_filename), open(self.output_filename, 'w')
        reader, writer = csv.reader(reader_f), csv.writer(writer_f)
        try:
            for row in reader:
                row[0] = '%09d' % groups[int(row[0])]
                writer.writerow(row)
        except Exception, e:
            print repr(e)

        reader_f.close()
        writer_f.close()

        del groups


def run(input_filename, output_filename):
    solr_merger = SolrMerger(input_filename, output_filename)
    try:
        solr_merger.run()
    finally:
        solr_merger.save_cache()

if __name__ == '__main__':
    import sys
    run(*sys.argv[1:3])
    #mergesort.run('../parsed/solr-grouped.csv', '../parsed/solr-grouped-sorted.csv')
