#
# Module to read out metadata from pkl files.
#
# by Heinrich Hartmann, related-work.net, 2012
#

import os, pickle, json

def get_json_from_dir(json_dir, limit = -1):
    counter = 0
    for file_name in os.listdir(json_dir):
        if not file_name.endswith('.json'): continue

        print "Processing", file_name

        try:
            fh = open(json_dir + file_name)
            objects = json.load(fh)
            fh.close()
        except (IOError, ValueError) as Err:
            print "Error loading json file", json_dir + file_name
            print Err
            continue

        for obj in objects:
            yield obj

            counter += 1
            if counter == limit:
                raise StopIteration


def get_meta_from_pkl(pkl_dir, limit = -1):
    """
    Reads arxiv meta records from *.pkl files in pkl_dir 
    and returns them as iterator (arxiv_id, meta_dict)
    """

    counter = 0
    for pkl_file_name in os.listdir(pkl_dir):
        if not pkl_file_name.endswith('.pkl'): continue

        print "Processing", pkl_file_name

        try:
            fh = open(pkl_dir + pkl_file_name)
            meta_list = pickle.load(fh)
            fh.close()
        except:
            print "Error loading pkl file", pkl_dir + pkl_file_name
            continue


        for oa_head,oa_meta,xxx in meta_list:
            try:
                oa_id = oa_head.identifier()
                meta_dict = oa_meta.getMap()
                # oa_id examples:
                # * 'oai:arXiv.org:astro-ph/0001516'
                # * 'oai:arXiv.org:1001.0231'
                # we remove the prefix 'oai:arXiv.org:'
                rec_id = oa_id.split(':')[-1]
            except:
                print "Error in record found in ", pkl_file_name
                continue

            yield rec_id, meta_dict

            counter += 1
            if counter == limit:
                raise StopIteration
