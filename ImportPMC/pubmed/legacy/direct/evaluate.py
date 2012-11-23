import sys, os
from itertools import chain
from pprint import pprint

from plugin_manager import Plugin_manager

def main(path):

    P = Plugin_manager()
    for filename in chain.from_iterable((os.path.join(x[0], f) for f in x[2]) for x in os.walk(path)):
        if not filename.endswith('.nxml'):
            continue

        info = P.handle(filename.split(os.path.sep)[-2],
                        filename,
                        components=['article_id', 'all_article_ids',
                                    'biblio', 'citations'])

        if len(info['biblio']['title']) > 20:
            continue

        print '%40s %s' % (filename.split('/')[-1], info['biblio']['title'].encode('utf-8'))
#        pprint(info)
#        break


if __name__ == '__main__':
    main(sys.argv[1])
        
