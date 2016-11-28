#!/bin/env python

'''
Convert all the 1-D XML examples to NXcanSAS
'''

import os
import xml2hdf5
import punx.h5structure

path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
os.chdir(path)
xml_files = [fn for fn in os.listdir('xml') if fn.lower().endswith('.xml')]
for xml_file_name in sorted(xml_files):
    hdf5_file = os.path.splitext(xml_file_name)[0] + '.h5'
    structure_file = os.path.join('structure', os.path.splitext(xml_file_name)[0] + '.h5.txt')
    
    converter = xml2hdf5.canSAS1D_to_NXcanSAS()
    converter.open_XML(os.path.join('xml', xml_file_name))
    converter.write_HDF5(hdf5_file)
    
    mc = punx.h5structure.h5structure(hdf5_file)
    structure = mc.report()
    fp = open(structure_file, 'w')
    fp.write('\n'.join(structure or ''))
    fp.close()
