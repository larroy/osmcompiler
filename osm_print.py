#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Just a tool to print Entities in an OSM dump"""
import sys
import os
import optparse

import osm
import osm.compiler
import osm.factory
import osm.sink

class PrintOSMSink(osm.sink.OSMSink):
    def __init__(self):
        pass

    def processNode(self, node):
        print node

    def processWay(self, way):
        print way

    def processRelation(self, rel):
        print rel

    def processMember(self, member):
        print member

def main():
    parser = optparse.OptionParser(usage = "%prog [options] osm_dump_file.pbf", version = "%prog 0.2")
    parser.add_option(
        "-q",
        "--quiet",
        action = "store_false",
        dest = "verbose",
        default = True,
        help = "don't print status messages to stdout")

    parser.add_option(
        "-f",
        "--from",
        dest = "frm",
        default = 0,
        type = 'int',
        help = "parse from this block onwards")

    parser.add_option(
        "-c",
        "--count",
        dest = "count",
        default = -1,
        type = 'int',
        help = "parse count blocks")

    (options, args) = parser.parse_args()

    if len(args) != 1:
        print "error: missing OSM dump file argument, run with --help option for help"
        return 1

    pbf_file = args[0]

    if not os.path.exists(pbf_file):
        sys.stderr.write('error: file {0} not found.\n'.format(pbf_file))
        return 1

    if options.verbose:
        print "Loading:", pbf_file

    with open(pbf_file, "rb") as fpbf:
        parser = osm.compiler.OSMCompiler(fpbf, PrintOSMSink(), osm.factory.OSMFactory(), options.verbose)
        parser.parse(options.frm, options.count)
        if options.verbose:
            for (k,v) in parser.count.items():
                print '{1} {0}'.format(k,v)

    return 0

if __name__ == '__main__':
    sys.exit(main())


