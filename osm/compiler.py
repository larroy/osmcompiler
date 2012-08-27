#!/usr/bin/env python
# -*- coding: utf-8 -*-

import fileformat_pb2
import osmformat_pb2
import osm
import sys
import os
from struct import unpack
import zlib
import logging
import collections
import pbar
import datetime

import factory

from . import Node, Way, Member, Relation

def read_int4(fd):
    """read an integer in network byte order and change to machine byte order. Return -1 if eof"""
    be_int = fd.read(4)
    if len(be_int) == 0:
        return -1
    else:
        le_int=unpack('!L',be_int)
        return le_int[0]


def skip_blobs(fd, N):
    count = 0
    blobHeader = fileformat_pb2.BlobHeader()
    assert(N >= 0)
    while count < N:
        blob_size = read_int4(fd)
        if blob_size <= 0:
            logging.warn('skipping past the last block')
            break

        blobHeader.ParseFromString(fd.read(blob_size))
        data_size = blobHeader.datasize
        if data_size <= 0:
            raise RuntimeError('Empty blobs are not allowed')
        fd.seek(data_size, os.SEEK_CUR)
        count += 1

def count_blobs(fd):
    count = 0
    blobHeader = fileformat_pb2.BlobHeader()
    while True:
        blob_size = read_int4(fd)
        if blob_size <= 0:
            break

        blobHeader.ParseFromString(fd.read(blob_size))
        data_size = blobHeader.datasize
        #print data_size, count
        if data_size <= 0:
            raise RuntimeError('Empty blobs are not allowed')
        else:
            fd.seek(data_size, os.SEEK_CUR)
            count += 1
    fd.seek(0)
    return count

class OSMCompiler:
    """Manage the process of parsing an osm.pbf file"""

    NANO = 1000000000L
    def __init__(self, filehandle, OSMSink, OSMFactory, verbose=False):
        """OSMCompiler constuctor
        """
        self.fpbf = filehandle
        self.verbose = verbose
        self.blobHeader = fileformat_pb2.BlobHeader()
        self.blob = fileformat_pb2.Blob()
        self.blobData = None
        self.hblock = osmformat_pb2.HeaderBlock()
        self.primblock = osmformat_pb2.PrimitiveBlock()
        self.membertype = {0:'node',1:'way',2:'relation'}
        self.count = collections.defaultdict(int)
        self.osm_sink = OSMSink
        self.osm_factory = OSMFactory

        if self.verbose:
            print 'Counting blobs (this might take a while for big dumps)...',
            sys.stdout.flush()
        self.nblobs = count_blobs(self.fpbf)
        self.ndatablobs = self.nblobs - 1
        if self.verbose:
            print ' {0}.'.format(self.nblobs)


        if not self.readBlob():
            return False

        #check the contents of the first blob are supported
        self.hblock.ParseFromString(self.blobData)
        for rf in self.hblock.required_features:
            if rf in ("OsmSchema-V0.6","DenseNodes"):
                pass
            else:
                raise RuntimeError('unknown feature {0}'.format(rf))

        if self.verbose:
            minlat = float(self.hblock.bbox.bottom) / OSMCompiler.NANO
            minlon = float(self.hblock.bbox.left) / OSMCompiler.NANO
            maxlat = float(self.hblock.bbox.top) / OSMCompiler.NANO
            maxlon = float(self.hblock.bbox.right) / OSMCompiler.NANO
            print 'Bounding Box (lat, lon): ({0},{1}) ({2},{3})'.format(minlat, minlon, maxlat, maxlon)

    def numDataBlobs(self):
        '''
        :returns number of blobs in the file
        :rtype int
        '''
        return self.ndatablobs

    def skipDataBlobs(self, n):
        '''
        :param n: number of blobs to skip
        '''
        assert(type(n) is int)
        skip_blobs(self.fpbf, n)

    def parse(self, fromblob=0, count=-1):
        """work through the data extracting OSM objects
        :param fromblob: limit processing to data blobs starting fromblob
        :param count: process this number of data blobs then return
        :returns None
        """
        if count < 0:
            count = self.ndatablobs - fromblob
        assert(type(count) is int)
        assert(count>=0)

        if fromblob:
            self.skipDataBlobs(fromblob)

        def prog():
                l = []
                for (k,v) in self.count.items():
                    l.append('{1} K {0} '.format(k, v // 1000))
                msg = '{0}/{1} blocks. '.format(nblob, count) + ' '.join(l) + pbar.est_finish(start, count, nblob)
                progress(nblob, msg)


        nblob = 0
        progress = pbar.ProgressBar(0, count)
        start = datetime.datetime.now()
        if self.verbose:
            prog()
        while nblob < count:
            size = self.readNextBlock()
            if not size:
                break
            for pg in self.primblock.primitivegroup:
                if len(pg.dense.id):
                    self.processDense(pg.dense)
                if len(pg.nodes):
                    self.processNodes(pg.nodes)
                if len(pg.ways):
                    self.processWays(pg.ways)
                if len(pg.relations):
                    self.processRels(pg.relations)

            nblob += 1
            if self.verbose:
                prog()

        if self.verbose:
            prog()
            print



    def readBlob(self):
        """Get the blob data, store the data for later"""
        blob_size = read_int4(self.fpbf)
        if blob_size <= 0:
            return False

        self.blobHeader.ParseFromString(self.fpbf.read(blob_size))

        if self.blobHeader.type not in ('OSMData', 'OSMHeader'):
            logging.error('Expected OSMData or OSMHeader, found %s', self.blobHeader.type)
            raise RuntimeError('expected OSMData or OSMHeader type')

        data_size = self.blobHeader.datasize
        if data_size <= 0:
            logging.warn('Empty Blob')
            return False

        self.blob.ParseFromString(self.fpbf.read(data_size))
        if self.blob.raw_size > 0:
            # uncompress the raw data
            self.blobData = zlib.decompress(self.blob.zlib_data, 15, self.blob.raw_size)
            decomp_size = len(self.blobData)
            if decomp_size != self.blob.raw_size:
                logging.warn("Corrupt block found decompressed size != raw_size field")
                assert(0)
        else:
            self.blobData = self.blob.raw
        return data_size

    def readNextBlock(self):
        """read the next block. Block is a header and blob, then extract the block"""
        size = self.readBlob()
        if size <= 0:
            return False

        # extract the primitive block
        self.primblock.ParseFromString(self.blobData)
        return size

    def processDense(self, dense):
        """process a dense node block"""
        # DenseNode uses a delta system of encoding os everything needs to start at zero
        lastID = 0
        lastLat = 0
        lastLon = 0
        tagloc = 0
        cs = 0
        ts = 0
        uid = 0
        user = 0
        gran = float(self.primblock.granularity)
        latoff = float(self.primblock.lat_offset)
        lonoff = float(self.primblock.lon_offset)
        for i in range(len(dense.id)):
            lastID +=  dense.id[i]
            lastLat +=  dense.lat[i]
            lastLon += dense.lon[i]
            lat = float(lastLat*gran+latoff) / OSMCompiler.NANO
            lon = float(lastLon*gran+lonoff) / OSMCompiler.NANO
            user += dense.denseinfo.user_sid[i]
            uid += dense.denseinfo.uid[i]
            vs = dense.denseinfo.version[i]
            ts += dense.denseinfo.timestamp[i]
            cs += dense.denseinfo.changeset[i]
            suser = self.primblock.stringtable.s[user]
            tm = ts*self.primblock.date_granularity/1000
            node = self.osm_factory.createNode(lastID)
            node.lon = lon
            node.lat = lat
            node.user = suser
            node.uid = uid
            node.version = vs
            node.changeset = cs
            node.time = tm
            if tagloc < len(dense.keys_vals):  # don't try to read beyond the end of the list
                while dense.keys_vals[tagloc] != 0:
                    ky = dense.keys_vals[tagloc]
                    vl = dense.keys_vals[tagloc+1]
                    tagloc += 2
                    sky = self.primblock.stringtable.s[ky]
                    svl = self.primblock.stringtable.s[vl]
                    node.addTag(sky,svl)
            tagloc += 1
            self.osm_sink.processNode(node)
        self.count['nodes'] += len(dense.id)

    def processNodes(self,nodes):
        print 'processNodes'
        gran = float(self.primblock.granularity)
        latoff = float(self.primblock.lat_offset)
        lonoff = float(self.primblock.lon_offset)
        for nd in nodes:
            lat = float(nd.lat * gran + latoff) / OSMCompiler.NANO
            lon = float(nd.lon * gran + lonoff) / OSMCompiler.NANO
            vs = nd.info.version
            ts = nd.info.timestamp
            uid = nd.info.uid
            user = nd.info.user_sid
            cs = nd.info.changeset
            tm = ts * self.primblock.date_granularity / 1000
            node = self.osm_factory.createNode(nd.id)
            node.lon = lon
            node.lat = lat
            node.user = suser
            node.uid = uid
            node.version = vs
            node.changeset = cs
            node.time = tm
            for i in range(len(nd.keys)):
                k = nd.keys[i]
                v = nd.vals[i]
                sk = self.primblock.stringtable.s[k]
                sv = self.primblock.stringtable.s[v]
                node.addTag(sk,sv)
            self.osm_sink.processNode(node)
        self.count['nodes'] += len(nodes)

    def processWays(self,ways):
        """process the ways in a block, extracting id, nds & tags"""
        for wy in ways:
            wayid = wy.id
            vs = wy.info.version
            ts = wy.info.timestamp
            uid = wy.info.uid
            user = self.primblock.stringtable.s[wy.info.user_sid]
            cs = wy.info.changeset
            tm = ts*self.primblock.date_granularity/1000
            way = self.osm_factory.createWay(wayid)
            way.user = user
            way.uid = uid
            way.version = vs
            way.changeset = cs
            way.time = tm
            ndid = 0
            for nd in wy.refs:
                ndid += nd
                way.addNode(ndid)
            for i in range(len(wy.keys)):
                ky = wy.keys[i]
                vl = wy.vals[i]
                sky = self.primblock.stringtable.s[ky]
                svl = self.primblock.stringtable.s[vl]
                way.addTag(sky,svl)
            self.osm_sink.processWay(way)
        self.count['ways'] += len(ways)

    def processRels(self,rels):
        for rl in rels:
            relid = rl.id
            vs = rl.info.version
            ts = rl.info.timestamp
            uid = rl.info.uid
            user = self.primblock.stringtable.s[rl.info.user_sid]
            cs = rl.info.changeset
            tm = ts*self.primblock.date_granularity/1000
            rel = self.osm_factory.createRelation(relid)
            rel.user = user
            rel.uid = uid
            rel.version = vs
            rel.changeset = cs
            rel.time = tm
            memid = 0
            for i in range(len(rl.memids)):
                role = rl.roles_sid[i]
                memid += rl.memids[i]
                memtype = self.membertype[rl.types[i]]
                memrole = self.primblock.stringtable.s[role]
                member = self.osm_factory.createMember(memtype,memid, memrole)
                rel.addMember(member)

            for i in range(len(rl.keys)):
                ky = rl.keys[i]
                vl = rl.vals[i]
                sky = self.primblock.stringtable.s[ky]
                svl = self.primblock.stringtable.s[vl]
                rel.addTag(sky,svl)
            self.osm_sink.processRelation(rel)
        self.count['relations'] += len(rels)

