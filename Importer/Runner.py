#!/usr/bin/env python
# encoding: utf-8
"""
Runner.py

Created by Martyn Whitwell on 2013-02-08.

to run, you will need the following Python libraries
pip install python-dateutil
pip install pyoai
pip install lxml (and probably libxslt2-dev and libxml on your machine)
pip install -U requests #Upgrades to the latest version of requests

"""

import sys
import os
import argparse
import OpenCitationsImportLibrary
import Config

def main(args):
    # Validate the parameters against the config again (better safe than sorry...)
    if args['action'] in Config.importer and args['source'] in Config.importer[args['action']]:
        importer_settings = Config.importer[args['action']][args['source']]
    else:
        print "Unknown action (%s) / source (%s) combination" % (args['action'], args['source'])
        sys.exit(1)

    # Clear the screen if the user specified the --clear flag
    if args['clear']:
        os.system('clear')

    print "OPEN CITATIONS IMPORTER"
    if (args['action']=="load"):
        print "Loading from source: %s" % importer_settings['name']
        if (args['identifier'] is not None):
            print "Warning: identifier option (%s) is ignored during the load operation" % (args['identifier'])
        if (args['from_date'] is not None):
            print "Warning: from-date option (%s) is ignored during the load operation" % (args['from_date'])
        if (args['to_date'] is not None):
            print "Warning: to-date option (%s) is ignored during the load operation" % (args['to_date'])
        if (args['rebuild']):
            print "Warning: index will be dropped and rebuilt. All existing records will be deleted."
        importer = OpenCitationsImportLibrary.PMCBulkImporter(importer_settings, args)
        importer.run()

    elif (args['action']=="synchronise"):
        print "Synchronising from source: %s" % importer_settings['name']
        print "Metadata format: %s" % importer_settings['metadata_format']
        print "Source Uri: %s" % importer_settings['uri']
        if (args['rebuild']):
            print "Warning: index will be dropped and rebuilt. All existing records will be deleted."
        if (args['identifier'] is not None):
            print "Limiting to identifier: %s" % (args['identifier'])
        if (args['from_date'] is not None):
            print "Limiting to from-date: %s" % (args['from_date'])
        if (args['to_date'] is not None):
            print "Limiting to to-date: %s" % (args['to_date'])
        importer = OpenCitationsImportLibrary.OAIImporter(importer_settings, args)
        importer.run()

    else:
        print "Unknown action: %s" % action
        sys.exit(1)

    print "Finished."
    sys.exit(0)


if __name__ == '__main__':
    # Define valid actions to perform
    actions = ["load", "synchronise"]
    # Define valid sources of data
    sources = list(set(Config.importer['synchronise'].keys() + Config.importer['load'].keys()))
    # Build argument parser
    parser = argparse.ArgumentParser(description='Open Citations Importer')
    parser.add_argument("-a", "--action", required=True, choices=actions, help="Importer action to perform: 'load' will bulk-load using local files; 'synchronise' will connect to an online OAI-PMH feed")
    parser.add_argument("-s", "--source", required=True, choices=sources, help="Source data repository to read from")
    parser.add_argument("-f", "--from", required=False, dest='from_date', help="Synchronise from the specified date (inclusive)")
    parser.add_argument("-t", "--to", required=False, dest='to_date', help="Synchronise to the specified date (inclusive)")
    parser.add_argument("-i", "--id", required=False, dest='identifier', help="Synchronise only the record specified by the given identifier")
    parser.add_argument("-R", "--REBUILD", action='store_const', dest='rebuild', const=True, required=False, default=False, help="Drop and rebuild the index. Use with care as all existing records will be deleted.")
    parser.add_argument("-c", "--clear", action='store_const', const=True, required=False, default=False, help="Clear the screen")

    args = vars(parser.parse_args())


    # Validate the arguments provided by the user with those supported in the Config
    if args['action'] in Config.importer and args['source'] in Config.importer[args['action']]:
        # Do some importing
        main(args)
    else:
        print "Unfortunately, action '%s' is not supported on source '%s'." % (args['action'], args['source'])
        print "Please refer to the importer definitions in Config.py for acceptable combinations."
