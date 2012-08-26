#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
import optparse


sys.path.append('minimongo')

# load mongodb credentials
import minimongo
import mongocredentials
minimongo.configure(module = mongocredentials)

import osm
import osm.compiler
import osm.factory
import osm.sink


class Node(osm.Node, minimongo.Model):
    pass

class Way(osm.Node, minimongo.Model):
    pass

class Relation(osm.Node, minimongo.Model):
    pass

class Member(osm.Node, minimongo.Model):
    pass

class MongoOSMFactory(osm.factory.OSMFactory):
    def createNode(self, id):
        return Node(id)

    def createWay(self, id):
        return Way(id)

    def createRelation(self, id):
        return Relation(id)

    def createMember(self, typ, id, role):
        return Member(typ, id, role)

class MongoOSMSink(osm.sink.OSMSink):
    def processNode(self, node):
        node.save()

    def processWay(self, way):
        way.save()

    def processRelation(self, rel):
        rel.save()

    def processMember(self, member):
        member.save()


def main():
    parser = optparse.OptionParser(usage="%prog [options] osm_dump_file", version="%prog 0.2")
    parser.add_option("-q", "--quiet",action="store_false", dest="verbose", default=True,help="don't print status messages to stdout")
    (options, args) = parser.parse_args()

    if len(args) != 1 :
        print "You must enter the binary filename (*.pbf)"
        sys.exit(1)

    pbf_file = args[0]

    if  not os.path.exists(pbf_file) :
        sys.stderr.write('error: file {0} not found.\n'.format(pbf_file))
        sys.exit(1)

    if options.verbose :
        print "Loading:", pbf_file

    fpbf = open(pbf_file, "rb")
    parser = osm.compiler.OSMCompiler(fpbf, MongoOSMSink(), MongoOSMFactory(), options.verbose)
    parser.parse()
    fpbf.close()

    if options.verbose:
        for (k,v) in parser.count.items():
            print '{1} {0}'.format(k,v)

if __name__ == '__main__':
    main()
