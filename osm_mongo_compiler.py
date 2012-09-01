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
import re
import unittest

def mongo_legal_key_escape(s):
    '''Make sure a string is a legal mongo key name, substitute unsafe characters'''
    l = []
    for c in s:
        if c == '%':
            l.append('%%')

        elif c == '~':
            l.append('~~')

        elif c == '^':
            l.append('^^')

        elif c == '$':
            l.append('%~')

        elif c == '.':
            l.append('%^')

        else:
            l.append(c)
    return ''.join(l)

def mongo_legal_key_unscape(s):
    l = []
    skipnext = False
    for (i,cur) in enumerate(s):
        next = None
        if skipnext:
            skipnext = False
            continue

        if i+1 < len(s):
            next = s[i+1]
        if cur == '%':
            if next:
                if next == '~':
                    l.append('$')
                    skipnext = True

                elif next == '%':
                    l.append('%')
                    skipnext = True

                elif next  == '^':
                    l.append('.')
                    skipnext = True

                else:
                    raise RuntimeError('unscaping unscaped string')

        elif cur == '~':
            if next:
                if next == '~':
                    l.append('~')
                    skipnext = True

                else:
                    raise RuntimeError('unscaping unscaped string')

        elif cur == '^':
            if next:
                if next == '^':
                    l.append('^')
                    skipnext = True

                else:
                    raise RuntimeError('unscaping unscaped string')

        else:
            l.append(cur)

    return ''.join(l)


class TestEscape(unittest.TestCase):
    def test_all(self):
        a = '$  pa $$ $  go %~ %% ~~ ~ %~%~  . .%^ %^^^^^'
        e = mongo_legal_key_escape(a)
        k = mongo_legal_key_unscape(e)
        self.assertEqual(a,k)

class Node(osm.Node, minimongo.Model):
    def addTag(self, k,v):
        k = mongo_legal_key_escape(k)
        super(Node, self).addTag(k, v)

class Way(osm.Way, minimongo.Model):
    def addTag(self, k,v):
        k = mongo_legal_key_escape(k)
        super(Way, self).addTag(k, v)
    pass

class Relation(osm.Relation, minimongo.Model):
    def addTag(self, k,v):
        k = mongo_legal_key_escape(k)
        super(Relation, self).addTag(k, v)
    pass

class Member(osm.Member, minimongo.Model):
    def addTag(self, k,v):
        k = mongo_legal_key_escape(k)
        super(Member, self).addTag(k, v)
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
    def __init__(self, verbose=0):
        self.verbose = verbose

    def processNode(self, node):
        if self.verbose:
            print node
        node.save()

    def processWay(self, way):
        if self.verbose:
            print way
        way.save()

    def processRelation(self, rel):
        if self.verbose:
            print rel
        rel.save()

    def processMember(self, member):
        if self.verbose:
            print member
        member.save()


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
        default = None,
        type = 'string',
        help = "show the number of data blocks (total- 1(header)")


    parser.add_option(
        "-n",
        "--num",
        dest = "num",
        default = -1,
        type = 'int',
        help = "parse num blocks")

    parser.add_option(
        "-t",
        "--test",
        dest = "test",
        default = 0,
        type = int,
        help = "run tests")

    parser.add_option(
        "-p",
        "--print",
        dest = "prnt",
        default = 0,
        type = int,
        help = "print objects to stdout as they are processed")



    (options, args) = parser.parse_args()

    if options.test:
        suite = unittest.TestLoader().loadTestsFromTestCase(TestEscape)
        unittest.TextTestRunner(verbosity=2).run(suite)
        return 0

    if len(args) != 1:
        print "error: missing OSM dump file argument, run with --help option for help"
        return 1

    pbf_file = args[0]

    if not os.path.exists(pbf_file):
        sys.stderr.write('error: file {0} not found.\n'.format(pbf_file))
        return 1

    if options.verbose:
        print "Loading:", pbf_file

    if options.count > 0:
        with open(pbf_file, "rb") as fpbf:
            parser = osm.compiler.OSMCompiler(fpbf, MongoOSMSink(options.prnt), MongoOSMFactory(), options.verbose)
            print "Number of data blobs: ", parser.numDataBlobs()
        return 0


    with open(pbf_file, "rb") as fpbf:
        parser = osm.compiler.OSMCompiler(fpbf, MongoOSMSink(options.prnt), MongoOSMFactory(), options.verbose)
        parser.parse(options.frm, options.num)
        if options.verbose:
            for (k,v) in parser.count.items():
                print '{1} {0}'.format(k,v)

    return 0

if __name__ == '__main__':
    sys.exit(main())


