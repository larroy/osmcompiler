#!/usr/bin/env python
# -*- coding: utf-8 -*-
from . import Node, Way, Relation, Member

class OSMFactory(object):
    '''Subclass and implement to create basic OSM types'''
    def createNode(self, id):
        return Node(id)

    def createWay(self, id):
        return Way(id)

    def createRelation(self, id):
        return Relation(id)

    def createMember(self, typ, id, role):
        return Member(typ, id, role)
