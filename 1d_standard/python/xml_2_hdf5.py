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


NS = dict(
    cs1_0 = 'cansas1d/1.0',
    cs1_1 = 'urn:cansas1d:1.1',
    xsi = 'http://www.w3.org/2001/XMLSchema-instance',
)


def openXML(xmlFile):
    '''
    '''
    if not os.path.exists(xmlFile):
        raise IOError('file not found: ' + xmlFile)
    
    doc = lxml.etree.parse(xmlFile)
    root = doc.getroot()
    # set the default XML namespace as 'cs'
    NS['cs'] = {'1.0': NS['cs1_0'], '1.1': NS['cs1_1']}[root.attrib['version']]
    return root


def convert(xmlFile, hdf5File):
    '''
    '''
    print xmlFile, hdf5File
    src = openXML(xmlFile)
    for sasentry in src.find('cs:SASentry'):
        node_name = sasentry.attrib.get('name', 'sasentry')
        print node_name


def developer():
    filelist = '''
    bimodal-test1.xml
    s81-polyurea.xml
    '''.strip().split()
    for fname in filelist:
        xmlFile = os.path.join('..', 'xml', 'bimodal-test1.xml')
        # demo(xmlFile)
        hdf5File = os.path.join('..', os.path.splitext(fname)[0] + '.h5')
        convert(xmlFile, hdf5File)


if __name__ == "__main__":
    developer()
