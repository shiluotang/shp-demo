#!/usr/bin/env python
# -*- coding: utf8 -*-


import zipfile
import sys
import io
import os
import binascii
import struct
import ctypes
import logging
import pprint


class ShpFileHeader(ctypes.BigEndianStructure):
    _pack_ = 1
    _fields_ = [
            ("FileCode", ctypes.c_int32),
            ("Unused1", ctypes.c_int32),
            ("Unused2", ctypes.c_int32),
            ("Unused3", ctypes.c_int32),
            ("Unused4", ctypes.c_int32),
            ("Unused5", ctypes.c_int32),
            # number of 16-bit WORDs (including 100 bytes Headers)
            ("FileLength", ctypes.c_int32),
            ]
    pass

class ShpMetaHeader(ctypes.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
            ("Version", ctypes.c_int32),
            ("ShapeType", ctypes.c_int32),
            ("Xmin", ctypes.c_double),
            ("Ymin", ctypes.c_double),
            ("Xmax", ctypes.c_double),
            ("Ymax", ctypes.c_double),
            ("Zmin", ctypes.c_double),
            ("Zmax", ctypes.c_double),
            ("Mmin", ctypes.c_double),
            ("Mmax", ctypes.c_double),
            ]
    pass


class RecordHeader(ctypes.BigEndianStructure):
    _pack_ = 1
    _fields_ = [
            ("RecordNumber", ctypes.c_int32),
            # number of 16-bit WORDs (only contents)
            ("ContentLength", ctypes.c_int32),
            ]
    pass

class Shape(object):
    _hex_ = True

    def parse(self, bytedata, offset = 0):
        self.Type,  = struct.unpack_from("<i", bytedata, offset)
        pass

    def __str__(self):
        return str(vars(self))

    def __repr__(self):
        return str(self)
    pass

    pass

class NullShape(Shape): pass

class PointShape():
    def parse(self, bytedata, offset = 0):
        super.parse(bytedata, offset)
        self.X, self.Y = struct.unpack_from("<2i", bytedata, offset + 4)
        pass
    pass

class MultiPoint(Shape):
    def parse(self, bytedata, offset = 0):
        Shape.parse(self, bytedata, offset)
        pass
    pass


class Polygon(Shape):
    def parse(self, bytedata, offset = 0):
        Shape.parse(self, bytedata, offset)
        # Xmin, Ymin, Xmax, Ymax
        self.Box = struct.unpack_from("<4d", bytedata, offset + 4)
        self.NumParts, self.NumPoints = struct.unpack_from(
                "<ii", bytedata, offset + 36)
        self.Parts = struct.unpack_from(
                "<" + str(self.NumParts) + "i",
                bytedata,
                offset + 44
                )
        self.Points = struct.unpack_from(
                "<" + str(self.NumPoints * 2) + "d",
                bytedata,
                offset + 44 + 4 * self.NumParts
                )
        pass
    pass


def containsPoint(box, lat, lon):
    return box[1] <= lat and box[3] >= lat \
            and box[0] <= lon and box[2] >= lon


def show_shp(zentry):
    headerBytes = zentry.read(ctypes.sizeof(ShpFileHeader) + ctypes.sizeof(ShpMetaHeader))
    print("SHP HEADER = %s" % (binascii.hexlify(headerBytes).upper()))
    fileHeader = ShpFileHeader.from_buffer_copy(headerBytes, 0)
    metaHeader = ShpMetaHeader.from_buffer_copy(headerBytes, ctypes.sizeof(ShpFileHeader))
    print("FileCode = %d, FileLength = %d (16-bit WORD, include HEADER)" % (fileHeader.FileCode, fileHeader.FileLength))
    print("Version = %d, ShapeType = %d, Xmin = %lf, Ymin = %lf, Xmax = %lf, Ymax = %lf, Zmin = %lf, Zmax = %lf" % (
        metaHeader.Version, metaHeader.ShapeType,
        metaHeader.Xmin, metaHeader.Ymin,
        metaHeader.Xmax, metaHeader.Ymax,
        metaHeader.Zmin, metaHeader.Zmax,
        ))

    # 16-bit word
    remain = fileHeader.FileLength * 2 - ctypes.sizeof(ShpFileHeader) - ctypes.sizeof(ShpMetaHeader);

    while remain > 0:
        #print("remain = %d" % (remain))
        recordHeaderBytes = zentry.read(ctypes.sizeof(RecordHeader))
        #print("RECORD HEADER = %s" % (binascii.hexlify(recordHeaderBytes).upper()))
        recordHeader = RecordHeader.from_buffer_copy(recordHeaderBytes)
        #print("RecordNumber = %d, ContentLength = %d (16-bit WORD)" % (recordHeader.RecordNumber, recordHeader.ContentLength * 2))
        content = memoryview(zentry.read(recordHeader.ContentLength * 2))
        polygon = Polygon()
        polygon.parse(content)
        if containsPoint(polygon.Box, 33, 108):
            print("%s, %s, %s" % (polygon.Box, polygon.NumParts, polygon.NumPoints))
        remain = remain - ctypes.sizeof(RecordHeader) - recordHeader.ContentLength * 2
    pass


if __name__ == '__main__':
    filename = "~/Downloads/gadm/gadm36_levels_shp.zip"
    path = os.path.expanduser(filename)

    if not zipfile.is_zipfile(path):
        print("Not zip file!")
        sys.exit(1)
    with zipfile.ZipFile(path, "r") as zfile:
        for info in zfile.infolist():
            if info.filename.startswith("gadm36_0"):
                if info.filename.endswith(".shp"):
                    with zfile.open(info, 'r') as zentry:
                        show_shp(zentry)

