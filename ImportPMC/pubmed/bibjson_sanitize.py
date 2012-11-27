from collections import defaultdict
import pprint
import re
import tarfile
import traceback
import urlparse
try:
    import cStringIO as StringIO
except ImportError:
    import StringIO

import simplejson

from bibjson_util import get_datasets, write_dataset


def run(input_filename, output_filename):
    tar_in = tarfile.open(input_filename, 'r:gz')
    tar_out = tarfile.open(output_filename, 'w:gz')

    j = k = 0
    for i, tar_info in enumerate(tar_in):
        data = tar_in.extractfile(tar_info)
        if tar_info.name.endswith('.json'):
            dataset = simplejson.load(data)
            for record in dataset['recordList']:
                errors = sanitize_record(record)
                if errors:
                    record['x-errors'] = errors
                    k += 1
                j += 1
            data = StringIO.StringIO()
            # simplejson.dump(dataset, data, indent='  ')
            simplejson.dump(dataset, data, indent=2)
            tar_info.size = data.tell()
            data.seek(0)
        tar_out.addfile(tar_info, data)

        if i % 10000 == 0:
            print "%10d %10d %10d" % (i, j, k)
            pprint.pprint(sorted(url_counts.iteritems(), key=lambda x:-x[1])[:10])

        tar_in.members, tar_out.members = [], []

VOLUME_SPLITS = map(re.compile, (
    ur'^(\d+)[ \(]+Pt (\d+)\)?$',
    ur'^(\d+) Suppl (\d+)$',
    ur'^(\d+);(\d+)$',
))

def sanitize_record(record):
    errors = record.get('x-errors', [])
    if record.get('volume'):
        sanitize_volume(record, errors)
    if record.get('issue'):
        sanitize_issue(record, errors)
    if record.get('uri'):
        record['url'] = record.pop('uri')
    if record.get('url'):
        sanitize_url(record, errors)
    if record.get('doi'):
        sanitize_doi(record, errors)
    return errors

def sanitize_volume(record, errors):
    original = record['volume']
    if not record.get('issue'):
       for volume_split in VOLUME_SPLITS:
           match = volume_split.match(original)
           if not match:
               continue

           record['volume'], record['issue'] = match.group(1, 2)
           errors.append({
               'fields': ('volume', 'issue'),
               'original': (original, None),
               'corrected': (record['volume'], record['issue']),
               'message': 'Split issue number out of volume',
           })
           original = record['volume']
           break

    if u'\u2212' in original:
        corrected = record['volume'] = original.replace(u'\u2212', '-')
        errors.append({
            'fields': ('volume',),
            'original': (original,),
            'corrected': (corrected,),
            'message': 'Replaced minus with hyphen',
        })
        original = corrected

    if u'\\' in original:
        errors.append({
            'fields': ('volume',),
            'original': (original,),
            'corrected': (original.replace('\\', ''),),
            'message': 'Removed backslash from volume',
        })
        original = record['volume'] = original.replace('\\', '')

def sanitize_issue(record, errors):
    original = record['issue']
    if original.startswith('Pt '):
        errors.append({
            'fields': ('issue',),
            'original': (original,),
            'corrected': (original[3:],),
            'message': "Removed 'Pt ' prefix from issue",
        })
        original = record['issue'] = original[3:]

    split = original.split()
    if split[1:2] == ['Pt']:
        corrected = split[0]
        errors.append({
            'fields': ('issue',),
            'original': (original,),
            'corrected': (corrected,),
            'message': 'Removed extraneous issue part information',
        })
        original = record['issue'] = corrected

DOI_RE = re.compile(r'^10\.\d{4}/.+$')
MISFORMATTED_DOI_RE = re.compile(r'^(?:10:|1.|)(\d{4}/.+)$')

def sanitize_doi(record, errors):
    doi = record['doi']
    match = MISFORMATTED_DOI_RE.match(doi)
    if match:
        corrected = '10.' + match.group(1)
        errors.append({
            'fields': ('doi',),
            'original': (doi,),
            'corrected': (corrected,),
            'message': 'Corrected DOI prefix',
        })
        doi = corrected
    elif not DOI_RE.match(record['doi']):
        errors.append({
            'fields': ('doi',),
            'original': (record['doi'],),
            'corrected': (None,),
            'message': 'Removed invalid DOI',
        })
        del record['doi']

DOMAIN_RE = re.compile(ur'^[a-z\d.-]+')
URL_DOI_RE = re.compile(ur'^http://dx\.doi\.org/(?:doi:)(.+)$')

url_counts = defaultdict(int)

def sanitize_url(record, errors):
    url = record['url']

    url = url.lstrip('[').rstrip('].')
    url = url.replace(u'\N{EN DASH}', '-') \
             .replace(u'\N{NO-BREAK SPACE}', '') \
             .replace(u'\N{TILDE OPERATOR}', '~') \
             .replace(u'http://http://', 'http://')

    if any(ord(c) > 127 for c in url):
        print "Non-ASCII:", url

    try:
        parsed = urlparse.urlparse(url)
    except:
        print url
        traceback.print_exc()
        errors.append({
            'fields': (u'url',),
            'original': (url,),
            'corrected': None,
            'message': 'Removed malformed URL',
        })
        del record['url']
        return

    if not parsed.scheme or parsed.netloc and DOMAIN_RE.match(parsed.path):
        try:
            parsed = urlparse.urlparse(u'http://%s' % parsed.path)
        except:
            print url
            raise
    if not parsed.netloc:
        parts = parsed.path.split(u'/', 1)
        netloc = parts[0]
        path = parts[1] if len(parts)>1 else u'/'
        parsed = parsed._replace(netloc=netloc, path=path)

    if not parsed.path:
        parsed = parsed._replace(path=u'/')

    parsed = parsed._replace(scheme=parsed.scheme.lower(),
                             netloc=parsed.netloc.lower())

    netloc_parts = parsed.netloc.split(u':')
    if len(netloc_parts) > 1:
        netloc_parts[1] = u''.join(c for c in netloc_parts[1] if c.isdigit())
    parsed = parsed._replace(netloc=u':'.join(netloc_parts))

    parsed = parsed._replace(netloc=u''.join(parsed.netloc.split()), path=parsed.path.rstrip('.'))

    new_url = parsed.geturl()

    match = URL_DOI_RE.match(new_url)
    if match:
        doi = match.group(1)
        del record[u'url']
        if record.get(u'doi'):
            errors.append({
                'fields': (u'url',),
                'original': (url,),
                'corrected': (None,),
                'message': u'Removed dx.doi.org URI',
            })
        else:
            record['doi'] = doi
            errors.append({
                'fields': (u'url', u'doi'),
                'original': (url, doi),
                'corrected': (None, doi),
                'message': u'Turned dx.doi.org URI into DOI',
            })
    elif url != new_url:
        errors.append({
            'fields': ('url'),
            'original': (url,),
            'corrected': (new_url,),
            'message': 'Corrected URL',
        })

    if not match:
        url_counts[new_url] += 1


if __name__ == '__main__':
    run('../parsed/articles-augmented.bibjson.tar.gz', '../parsed/articles-sanitized.bibjson.tar.gz')
