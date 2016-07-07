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
        eznx.addAttributes(nx_root, 
                           creator='xml_2_hdf5.py')
        print self.xmlFile
        group_list = self.process_sasentry(self.root, nx_root)
        if len(group_list) > 0:
            default = group_list[0].name.split('/')[-1]
            eznx.addAttributes(nx_root, default=default)
        nx_root.close()

    def process_sasentry(self, xml_parent, nx_parent):
        '''
        process any SASentry groups
        '''
        nx_entries = []
        x_groups = xml_parent.findall('cs:SASentry', self.ns)
        for i, x_sasentry in enumerate(x_groups):
            nm = safename(x_sasentry.attrib.get('name', 
                                                'sasentry_'+str(i)))
            print nm
            nxentry = eznx.makeGroup(nx_parent, 
                                        nm, 'NXentry',
                                        canSAS_class='SASentry')
            nx_entries.append(nxentry)

            group_list = self.process_sasdata(x_sasentry, nxentry)
            if len(group_list) > 0:
                default = group_list[0].name.split('/')[-1]
                eznx.addAttributes(nxentry, default=default)

        return nx_entries

    def process_sasdata(self, xml_parent, nx_parent):
        '''
        process any SASdata groups
        '''
        nx_group_list = []
        x_groups = xml_parent.findall('cs:SASdata', self.ns)
        for i, x_sasentry in enumerate(x_groups):
            nm = safename(x_sasentry.attrib.get('name', 
                                                'sasdata_'+str(i)))
            print nm
            nxdata = eznx.makeGroup(nx_parent, 
                                    nm, 'NXdata',
                                    canSAS_class='SASdata')
            nx_group_list.append(nxdata)
        return nx_group_list


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
