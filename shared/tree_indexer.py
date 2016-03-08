#!/usr/bin/env python

import os
import json
import re

import tree_functions

# Functions
functions = tree_functions.TreeFunctions()


class Index(object):
    """docstring for Index"""
    def __init__(self, logger, constants):
        super(Index, self).__init__()

        self.c = constants

        # Log
        logger.info('Indexing started at ' + unicode(self.c['now_timestamp']))
        logger.info('Source dir: ' +
                    functions.enc(os.path.abspath(self.c['src_dir'])))
        logger.info('Log file: ' +
                    functions.enc(os.path.abspath(self.c['log_file'])))

        # Indexing
        index = self.indexer()  # traverse
        self.write_json(data=index)  # dump index to disk

    def indexer(self):
        """ Index the directory

        Algorithm:
        - If no limits, will delete all files
        - If limit by --days ...
        - If limit by --regex ...
        - If limit by --days AND --regex ...

        This means that algo drivers are 'DAYS' and 'REGEX' variables.

        """
        if self.c['days'] == self.c['default_days'] and \
                self.c['regex'] == self.c['default_regex']:
            # no limits, will delete all files
            index = self.traverse(limit=[])
        elif self.c['days'] != self.c['default_days'] and \
                self.c['regex'] == self.c['default_regex']:
            # limit by days
            index = self.traverse(limit=['days'])
        elif self.c['days'] == self.c['default_days'] and \
                self.c['regex'] != self.c['default_regex']:
            # limit by regex
            index = self.traverse(limit=['regex'])
        elif self.c['days'] != self.c['default_days'] and \
                self.c['regex'] != self.c['default_regex']:
            # limit by BOTH days and regex
            index = self.traverse(limit=['days', 'regex'])

        return index

    def traverse(self, limit):
        """ Based on indexer method, directory will be traversed and files
        will get registered to get deleted.
        """
        index = {}  # json dictionary
        for root, dirs, files in os.walk(unicode(self.c['src_dir'])):
            path = root.split('/')
            if not self.c['silent']:
                print (len(path) - 1) * '-', os.path.basename(root)

            items = files + dirs
            for i in items:
                item_registered = False
                filepath = os.path.join(root, i)

                if 'days' not in limit and 'regex' not in limit:
                    index[filepath] = {}
                    item_registered = True

                elif 'days' in limit and 'regex' not in limit:
                    timestamp = functions.modification_date(filepath=filepath)
                    keep = functions.keep(
                            now_timestamp=self.c['now_timestamp'],
                            timestamp=timestamp,
                            days=self.c['days'])
                    if not keep:
                        # Add filepath to index
                        if filepath not in index:
                            index[filepath] = {}
                        index[filepath]['t'] = unicode(timestamp)
                        item_registered = True

                elif 'days' not in limit and 'regex' in limit:
                    match = re.search(r''+self.c['regex']+'', filepath)
                    if match:
                        if filepath not in index:
                            index[filepath] = {}
                        index[filepath]['r'] = 'True'
                        item_registered = True

                elif 'days' in limit and 'regex' in limit:
                    timestamp = functions.modification_date(filepath=filepath)
                    keep = functions.keep(
                            now_timestamp=self.c['now_timestamp'],
                            timestamp=timestamp,
                            days=self.c['days'])
                    if not keep:
                        match = re.search(r''+self.c['regex']+'', filepath)
                        if match:
                            if filepath not in index:
                                index[filepath] = {}
                            index[filepath]['r'] = 'True'
                            item_registered = True

                if item_registered:
                    if self.c['tool'] == 'tree_purger':
                        b = self.file_size(filepath=filepath)
                        index[filepath]['b'] = b
                    elif self.c['tool'] == 'tree_leafsize':
                        if os.path.isdir(filepath):
                            b = self.folder_tree_size(filepath=filepath)
                        else:
                            b = self.file_size(filepath=filepath)
                        index[filepath]['b'] = b

                    if not self.c['silent']:
                        size = functions.nice_number(b=b)
                        print len(path)*'-', i, '('+size+')'

        return index

    def file_size(self, filepath):
        # File size in bytes
        b = os.stat(filepath).st_size
        return b

    def folder_tree_size(self, filepath):
        # Folder tree size in bytes
        b = self.file_size(filepath)
        for root, dirs, files in os.walk(filepath):
            items = dirs + files
            for i in items:
                fp = os.path.join(root, i)
                b += os.stat(fp).st_size
        return b

    def write_json(self, data):
        with open(self.c['index_file'], 'w') as outfile:
            json.dump(data, outfile, sort_keys=True, indent=4,
                      separators=(',', ': '))