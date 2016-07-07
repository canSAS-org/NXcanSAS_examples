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
from spec2nexus import eznx


def safename(text):
    '''
    make sure text conforms to NeXus relaxed validItemName
    
    reg exp:  [A-Za-z_][\w_]*
    '''
    return text.replace(' ', '_')  # TODO: generalize


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
        self.ns['cs'] = {'1.0': self.ns['cs1_0'],
                         '1.1': self.ns['cs1_1']}[self.root.attrib['version']]
    
    def write(self, hdf5File):
        '''
        write the HDF5 file while parsing the XML file
        '''
        nx_root = eznx.makeFile(hdf5File)
        eznx.addAttributes(nx_root, creator='canSAS1d_to_NXcanSAS.py')
        print self.xmlFile
        x_sasentries = self.root.findall('cs:SASentry', self.ns)
        default = None
        for i, x_sasentry in enumerate(x_sasentries):
            nm = safename(x_sasentry.attrib.get('name', 'sasentry_'+str(i)))
            print nm
            if default is None:
                default = nm
                eznx.addAttributes(nx_root, default=nm)
            nx_sasdata = eznx.makeGroup(nx_root, 
                                        nm, 'NXentry',
                                        canSAS_class='SASentry')
        nx_root.close()

#         for node in self.root:
#             if node.tag.endswith('}SASentry'):
#                 node_name = node.attrib.get('name', 'x_sasentry')
#                 print node_name

    def p_sasentry(self):
        '''
        '''


def developer():
    filelist = '''
    bimodal-test1.xml
    s81-polyurea.xml
    1998spheres.xml
    '''.strip().split()
    # filelist = os.listdir(os.path.join('..', 'xml'))
    for fname in filelist:
        if fname.endswith('.xml'):
            xmlFile = os.path.join('..', 'xml', fname)
            converter = canSAS1D_to_NXcanSAS()
            converter.open(xmlFile)
            hdf5File = os.path.join('..', os.path.splitext(fname)[0] + '.h5')
            converter.write(hdf5File)


if __name__ == "__main__":
    developer()
