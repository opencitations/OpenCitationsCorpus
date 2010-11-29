#!/usr/bin/env python
# -*- coding=utf-8 -*-

from __future__ import division

import sys, os
from collections import defaultdict
from pprint import pprint

from plugin_manager import Plugin_manager
from create_network import generate_network

def avg(iterable):
    iterator = iter(iterable)
    sum_, count = iterator.next(), 1
    for i in iterator:
        sum_ += i
        count += 1
    return sum_ / count

if __name__ == '__main__':

    journal_attribs = defaultdict(dict)
    for i, path in enumerate(os.listdir(sys.argv[1])):
        print '%4d %s' % (i, path)

        try:
            g = generate_network(os.path.join(sys.argv[1], path))

            attribs = defaultdict(lambda:[0,0])
    
            for n in g.nodes():
                for k,v in g.node[n].items():
                    attribs[k][0 if v else 1] += 1
    
            attribs = [(k, v[0]/sum(v)) for k, v in attribs.items()]
    
            for k, v in attribs:
                journal_attribs[k][path] = v
        except KeyboardInterrupt:
            break



    journal_attribs = list(journal_attribs.items())
    journal_attribs.sort(key=lambda a: avg(a[1].values()))
    journal_attribs = [(k, sorted(v.items(), key=lambda x:x[1])) for k,v in journal_attribs]
    
    pprint(journal_attribs, stream=open('fields_found.txt', 'w'))
    pprint(journal_attribs)

