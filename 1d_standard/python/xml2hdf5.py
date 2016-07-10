#!/usr/bin/env python

'''
*xml2hdf5.py* : convert canSAS1d XML file to NXcanSAS HDF5 file

This is a standalone Python program to read any canSAS1d XML data file
(either v1.0 or v1.1) and convert it to a NeXus HDF5 data file according
to the NXcanSAS application definition (currently a contributed definition).

:see: http://download.nexusformat.org/doc/html/classes/contributed_definitions/NXcanSAS.html
'''

# Copyright (c) 2013-2016, UChicago Argonne, LLC
# This file is distributed subject to a Software License Agreement found
# in the file LICENSE that is included with this distribution. 


import os
import sys
import lxml.etree
from spec2nexus import eznx, utils


class canSAS1D_to_NXcanSAS(object):
    '''
    manage conversion of one canSAS1d file to one NXcanSAS file
    
    .. rubric:: Usage
    
    >>> import xml2hdf
    >>> converter = xml2hdf.canSAS1D_to_NXcanSAS()
    >>> converter.open_XML(xmlFile)
    >>> converter.write_HDF5(hdf5File)

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
    
    def open_XML(self, xmlFile):
        '''
        open the canSAS1d XML data file, raise IOError if not found
        '''
        if not os.path.exists(xmlFile):
            raise IOError('file not found: ' + xmlFile)
        self.xmlFile = xmlFile
        self.root = lxml.etree.parse(xmlFile).getroot()
        self.ns['cs'] = {'1.0': self.ns['cs1_0'],
                         '1.1': self.ns['cs1_1']}[self.root.attrib['version']]
    
    def write_HDF5(self, hdf5File):
        '''
        write_ the HDF5 file *while parsing* the XML file
        '''
        nx_root = eznx.makeFile(hdf5File)
        eznx.addAttributes(nx_root, creator='xml2hdf5.py')
        group_list = self.process_SASentry(self.root, nx_root)
        if len(group_list) > 0:
            default = group_list[0].name.split('/')[-1]
            eznx.addAttributes(nx_root, default=default)
        nx_root.close()

    def process_SASentry(self, xml_parent, nx_parent):
        '''
        process any SASentry groups
        '''
        nx_node_list = []
        x_groups = xml_parent.findall('cs:SASentry', self.ns)
        for i, sasentry in enumerate(x_groups):
            nm = sasentry.attrib.get('name', 'sasentry_'+str(i))
            nxentry = eznx.makeGroup(nx_parent, 
                                        utils.clean_name(nm), 'NXentry',
                                        canSAS_class='SASentry')
            nx_node_list.append(nxentry)
            eznx.makeDataset(nxentry, 'definition', 'NXcanSAS')

            group_list = self.process_SASdata(sasentry, nxentry)
            if len(group_list) > 0:
                default = group_list[0].name.split('/')[-1]
                eznx.addAttributes(nxentry, default=default)
            self.process_Run(sasentry, nxentry)
            
            for xmlnode in sasentry:
                if xmlnode.tag.endswith('}Title'):
                    eznx.makeDataset(nxentry, 'title', xmlnode.text)
                elif xmlnode.tag.endswith('}Run'):
                    pass            # already handled above
                elif xmlnode.tag.endswith('}SASdata'):
                    pass            # already handled above
                elif xmlnode.tag.endswith('}SASsample'):
                    pass            # TODO: SASsample
                elif xmlnode.tag.endswith('}SASinstrument'):
                    pass            # TODO: SASinstrument
                elif xmlnode.tag.endswith('}SASnote'):
                    pass            # TODO: SASnote
                elif xmlnode.tag.endswith('}SASprocess'):
                    pass            # TODO: SASprocess
                elif xmlnode.tag.endswith('}SAStransmission_spectrum'):
                    pass            # TODO: SASprocess
                else:
                    # such as:
                    '''
                    <Run_extension xmlns="ILL-data">001</Run_extension>
                    <Source_file xmlns="ILL-data">"g009036.001"</Source_file>
                    <Flux_monitor xmlns="ILL-data">1.00</Flux_monitor>
                    <Count_time_secs xmlns="ILL-data">886.200</Count_time_secs>
                    <Q_resolution xmlns="ILL-data">"estimated"</Q_resolution>
                    '''
                    raise KeyError('unexpected SASentry tag: ' + xmlnode.tag)

        return nx_node_list

    def process_Run(self, xml_parent, nx_parent):
        '''
        process any Run elements
        '''
        xml_node_list = xml_parent.findall('cs:Run', self.ns)
        for i, xmlnode in enumerate(xml_node_list):
            nm = 'run'
            if len(xml_node_list) > 0:
                nm += '_' + str(i)
            eznx.makeDataset(nx_parent, nm, xmlnode.text)
            eznx.addAttributes(nx_parent, **{k: v for k, v in xmlnode.attrib.items()})

    def process_SASdata(self, xml_parent, nx_parent):
        '''
        process any SASdata groups
        '''
        nx_node_list = []
        xml_node_list = xml_parent.findall('cs:SASdata', self.ns)
        for i, sasdata in enumerate(xml_node_list):
            nm = 'sasdata'
            if len(xml_node_list) > 1:
                nm += '_' + str(i)
            nm = sasdata.attrib.get('name', nm)
            nxdata = eznx.makeGroup(nx_parent, 
                                    utils.clean_name(nm), 'NXdata',
                                    canSAS_class='SASdata')
            nx_node_list.append(nxdata)
            
            # collect the SAS data arrays
            data = {}
            units = {}
            for xmlnode in sasdata:
                try:
                    if xmlnode.tag.endswith('}Idata'):
                        for xmldata in xmlnode:
                            try:
                                tag = xmldata.tag.split('}')[-1]
                            except AttributeError, _exc:
                                continue        # an XML comment triggered this
                            if tag not in data:
                                data[tag] = []
                                units[tag] = xmldata.get('unit', None)
                            data[tag].append(xmldata.text)
                    else:
                        raise KeyError('unexpected SASdata tag: ' + xmlnode.tag)
                except AttributeError, _exc:
                    continue        # XML Comment
            
            # write the data arrays
            nx_obj = {}
            for nm, arr in data.items():
                try:
                    nx_obj[nm] = eznx.makeDataset(nxdata, nm, map(float, data[nm]), units=units[nm])
                except TypeError, _exc:
                    pass
            
            # set the NeXus plottable data attributes
            if 'I' in data:
                eznx.addAttributes(nxdata, signal='I')
                if 'Q' in data:
                    eznx.addAttributes(nxdata, I_axes='Q')        # NeXus
                if 'Idev' in data:
                    eznx.addAttributes(nxdata, I_uncertainty='Idev')        # canSAS
                    eznx.addAttributes(nx_obj['I'], uncertainty='Idev')     # NeXus

        return nx_node_list


def developer():
    from spec2nexus import h5toText
    filelist = '''
    bimodal-test1.xml
    s81-polyurea.xml
    1998spheres.xml
    '''.strip().split()
    filelist = os.listdir(os.path.join('..', 'xml'))    # TODO: what about .XML?
    for fname in filelist:
        if fname.find('cansas1d-template.xml') >= 0:
            continue
        if fname.find('cansas1d.xml') >= 0:
            continue
        if fname.endswith('.xml'):
            xmlFile = os.path.join('..', 'xml', fname)
            converter = canSAS1D_to_NXcanSAS()
            converter.open_XML(xmlFile)
            hdf5File = os.path.join('..', os.path.splitext(fname)[0] + '.h5')
            converter.write_HDF5(hdf5File)
            
            mc = h5toText.H5toText(hdf5File)
            print '-'*30
            print fname
            print '\n'.join(mc.report() or '')


def main():
    '''
    standard command line interface
    '''


if __name__ == "__main__":
    developer()
