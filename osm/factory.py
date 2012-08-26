#!/usr/bin/env python
# -*- coding: utf-8 -*-

class OSMFactory(object):
    '''Subclass and implement to create basic OSM types'''
    def createNode(self):
        raise NotImplementedError()

    def createWay(self):
        raise NotImplementedError()

    def createRelation(self):
        raise NotImplementedError()

    def createMember(self):
        raise NotImplementedError()

