#!/usr/bin/env python
# -*- coding: utf-8 -*-

__all__ = ('sink', 'factory')

class Node(object):
    def __init__(self, id = 0):
        self._id = id
        self.lon = 0.0
        self.lat = 0.0
        self.version = 0
        self.time = 0
        self.uid = 0
        self.user = ""
        self.changeset = 0

    def addTag(self, k, v):
        try:
            self.tags[k] = v
        except AttributeError:
            self.tags = {}
            self.tags[k] = v


    def __str__(self):
        res = []
        res.append('Node {0}: ({1}, {2})\n'.format(self._id, self.lat, self.lon))
        for t in self.tags.keys():
            res.append('\t{0} = {1}\n'.format(t, self.tags[t]))
        return ''.join(res)

class Way(object):
    def __init__(self, id = 0):
        self._id = id
        self.time = 0
        self.uid = 0
        self.user = ""
        self.changeset = 0
        self.tags = {}
        self.nodes = []

    def addTag(self, k, v):
        self.tags[k] = v

    def addNode(self, nodeid):
        self.nodes.append(nodeid)

    def __str__(self):
        res = ['Way {0}:\n\tnodes:'.format(self._id)]
        res.append(', '.join(map(lambda x: str(x), self.nodes)))
        res.append('\n')
        for t in self.tags.keys():
            res.append('\t{0} = {1}\n'.format(t, self.tags[t]))
        return ''.join(res)

class Member(object):
    def __init__(self, type, ref, role):
        self.type = type
        self.ref = ref
        self.role = role

    def __str__(self):
        return 'Member {0}, {1}, {2}'.format(self.type, self.ref, self.role)

class Relation(object):
    def __init__(self, id = 0):
        self._id = id
        self.time = 0
        self.uid = 0
        self.user = ""
        self.changeset = 0
        self.tags = {}
        self.members = []

    def addTag(self, k, v):
        self.tags[k] = v

    def addMember(self, member):
        self.members.append(member)

    def __str__(self):
        res = ['Relation {0}:\n\t'.format(self._id)]
        res.append('\n\t'.join(map(lambda x: str(x), self.members)))
        return ''.join(res)



