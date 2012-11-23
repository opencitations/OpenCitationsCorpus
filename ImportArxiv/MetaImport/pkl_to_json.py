from MetaRead import get_meta_from_pkl

import sys
sys.path.append('../tools')
from shared import group_generator

import json

for i, batch in enumerate(group_generator(get_meta_from_pkl('../DATA/META/PKL/'),10000)):
    fh = open('../DATA/META/JSON/META_%03d.json' % i, 'w')
    json.dump(batch,fh)
    fh.close()
