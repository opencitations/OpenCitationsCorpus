from __future__ import division

from collections import defaultdict

import resource, sys, traceback
import tarfile, simplejson, tempfile, itertools, os, StringIO, pprint

from bibjson_util import get_records
from merge_sort import run as merge_sort

IDENTIFIERS = ('pmid', 'doi', 'pmc', 'uri', 'patent_number', 'isbn', 'issn', 'eissn', 'x-nlm-ta')

def tidy_identifier(scheme, value):
    if scheme == 'x-nlm-ta':
        return scheme, ' '.join(value.lower().replace('.', '').split())
    return scheme, value

def run(input_filename, output_filename):
    tar = tarfile.open(input_filename, 'r:gz')
    record_file = tempfile.NamedTemporaryFile(delete=False)

    articles, without_identifiers = defaultdict(set), set()
    biggest = 0

    try:
        for i, (_, record) in enumerate(get_records(tar, types=("Article", "Journal"))):
            identifiers = [tidy_identifier(k, record[k]) for k in record if k in IDENTIFIERS and record.get(k)]
            if not identifiers:
                without_identifiers.add(record['id'])
                continue
            articles[identifiers[0]].add(record['id'])
            for identifier in identifiers[1:]:
                if articles[identifiers[0]] is not articles[identifier]:
                    articles[identifiers[0]] |= articles[identifier]
                    articles[identifier] = articles[identifiers[0]]
                    if len(articles[identifier]) > biggest:
                        biggest = len(articles[identifier])

            if i % 10000 == 0:
                print "%7d" % i
    except BaseException, e:
        traceback.print_exc()

    tar.close()
    tar = tarfile.open(input_filename, 'r:gz')

    articles = dict((id(l), l) for l in articles.values()).values()
    groups = {}
    for i, article_list in enumerate(articles):
        for article_id in article_list:
            groups[article_id] = i
    for article in without_identifiers:
        i += 1
        groups[article] = i

    del without_identifiers, articles

    RELATIONS = 'affiliated publisher author editor translator'.split()

    try:
        for i, (index, record) in enumerate(get_records(tar, True, types=('Article', 'Journal'))):
            #pprint.pprint(index)
            records, group = [], groups[record['id']]
            to_add, queue, data = set(), set([record['id']]), {'group': group, 'records': records}

            while queue:
                id_ = queue.pop()
                record = index[id_]
                to_add.add(id_)
                for id_ in itertools.chain(*[(lambda x:(x if isinstance(x, list) else [x]))(record.get(k, [])) for k in RELATIONS]):
                    print id_
                    id_ = id_['ref'][1:]
                    if id_ not in to_add:
                        queue.add(id_)

            for id_ in to_add:
                records.append(index[id_])
            record_file.write('%010d %s\n' % (group, simplejson.dumps(data)))

            if i % 10000 == 0:
                print "%7d" % i
    except BaseException, e:
        traceback.print_exc()

    record_file.close()

    fh, sorted_record_filename = tempfile.mkstemp()
    os.close(fh)
    merge_sort(record_file.name, sorted_record_filename)
    os.unlink(record_file.name)

    del index, to_add, queue, groups, record, identifier, identifiers, i, k, biggest, records, record_file, fh, data, article_list, article, article_id, group
    print list(locals())

    tar.close()
    tar = tarfile.open(output_filename, 'w:gz')

    try:
        for i, (group, lines) in enumerate(itertools.groupby(open(sorted_record_filename), lambda l:l.split(' ', 1)[0])):
            lines = list(lines)
#            print i, group, len(lines), resource.getrusage(resource.RUSAGE_SELF)[2]

            records = list(itertools.chain(*[simplejson.loads(line.split(' ', 1)[1])['records'] for line in lines]))

            dataset = {
                'dataset': {},
                'recordList': records,
            }

            for record in records:
                if record['type'] in ('Article', 'Journal'):
                    ptype = record['type']
                    break
            else:
                ptype = "Unknown"

            for record in records:
                if 'x-nlm-ta' in record:
                    filename = ' '.join(record['x-nlm-ta'].replace('.', '').split()).title().replace(' ', '_')
                    break
            else:
                filename = '%s/%s' % (group[-4:], group)

            tar_info = tarfile.TarInfo("%s/%s.json" % (ptype, filename))
            data = StringIO.StringIO()
            data.write(simplejson.dumps(dataset))
            tar_info.size = data.len
            data.seek(0)
            tar.addfile(tar_info, data)

            if i % 10000 == 0:
                tar.members = []
                print "%7d" % i, resource.getrusage(resource.RUSAGE_SELF)[2]
                #l = locals()
                #for k in l:
                #    print "%20s %10d" % (k, sys.getsizeof(l[k]))

    except BaseException, e:
        traceback.print_exc()

    tar.close()


if __name__ == '__main__':
    run('../parsed/articles-augmented.bibjson.tar.gz', '../parsed/articles-unified.bibjson.tar.gz')


