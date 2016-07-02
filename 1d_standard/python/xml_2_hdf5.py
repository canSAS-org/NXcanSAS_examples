#!/usr/bin/env python

'''
convert canSAS1d XML file to NXcanSAS HDF5 file
'''

# Copyright (c) 2013-2016, UChicago Argonne, LLC
# This file is distributed subject to a Software License Agreement found
# in the file LICENSE that is included with this distribution. 


import os
import sys
import lxml.etree
#from spec2nexus import eznx


class canSAS1D_to_NXcanSAS(object):
    '''
    '''
    
    def __init__(self):
        self.ns = dict(
            cs1_0 = 'cansas1d/1.0',
            cs1_1 = 'urn:cansas1d:1.1',
            xsi = 'http://www.w3.org/2001/XMLSchema-instance',
        )
        self.xmlFile = None
        self.hdf5File = None
        self.root = None
    
    def open(self, xmlFile):
        '''
        '''
        if not os.path.exists(xmlFile):
            raise IOError('file not found: ' + xmlFile)
        self.xmlFile = xmlFile
        self.root = lxml.etree.parse(xmlFile).getroot()
    
    def write(self, hdf5File):
        '''
        '''
        for node in self.root:
            if node.tag.endswith('}SASentry'):
                node_name = node.attrib.get('name', 'sasentry')
                print node_name
#     nx_root = eznx.makeFile(hdf5File)
#     eznx.addAttributes(nx_root, creator='canSAS1d_to_NXcanSAS.py')


def developer():
    filelist = '''
    bimodal-test1.xml
    s81-polyurea.xml
    '''.strip().split()
    for fname in filelist:
        xmlFile = os.path.join('..', 'xml', 'bimodal-test1.xml')
        converter = canSAS1D_to_NXcanSAS()
        converter.open(xmlFile)
        hdf5File = os.path.join('..', os.path.splitext(fname)[0] + '.h5')
        converter.write(hdf5File)


if __name__ == "__main__":
    developer()
