#!/usr/bin/env python
# -*- coding: utf-8 -*-

class OSMSink(object):
    '''Subclass and implement methods to process OSM instances'''
    def processNode(self, node):
        raise NotImplementedError()

    def processWay(self, way):
        raise NotImplementedError()

    def processRelation(self, rel):
        raise NotImplementedError()

    def processMember(self, member):
        raise NotImplementedError()



