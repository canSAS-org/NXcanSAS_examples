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

            # process the groups that may appear more than once
            group_list = self.process_SASdata(sasentry, nxentry)
            if len(group_list) > 0:
                default = group_list[0].name.split('/')[-1]
                eznx.addAttributes(nxentry, default=default)

            self.process_Run(sasentry, nxentry)
            
            self.process_SAStransmission_spectrum(sasentry, nxentry)
            
            # process any other items
            for xmlnode in sasentry:
                if xmlnode.tag.endswith('}Title'):
                    eznx.makeDataset(nxentry, 'title', xmlnode.text)
                elif xmlnode.tag.endswith('}Run'):
                    pass            # already handled above
                elif xmlnode.tag.endswith('}SASdata'):
                    pass            # already handled above
                elif xmlnode.tag.endswith('}SASsample'):
                    self.process_SASsample(xmlnode, nxentry)
                elif xmlnode.tag.endswith('}SASinstrument'):
                    pass            # TODO: SASinstrument
                elif xmlnode.tag.endswith('}SASnote'):
                    pass            # TODO: SASnote
                elif xmlnode.tag.endswith('}SASprocess'):
                    pass            # TODO: SASprocess
                elif xmlnode.tag.endswith('}SAStransmission_spectrum'):
                    pass            # already handled above
                else:
                    self.process_unexpected_xml_element(xmlnode, nxentry)

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
            self.copy_attributes(xml_parent, nx_parent)

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
                                    canSAS_class='SASdata',
                                    canSAS_name=nm)
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
                                units[tag] = xmldata.get('unit', 'none')
                            data[tag].append(xmldata.text)
                    else:
                        self.process_unexpected_xml_element(xmlnode, nxdata)
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

    def process_SAStransmission_spectrum(self, xml_parent, nx_parent):
        '''
        process any SAStransmission_spectrum groups
        
        These are handled similar to SASdata with different nouns
        
        Shouldn't this be located (in NeXus) at /NXentry/NXsample/transmission?
        '''
        nx_node_list = []
        xml_node_list = xml_parent.findall('cs:SAStransmission_spectrum', self.ns)
        for i, sas_ts in enumerate(xml_node_list):
            nm = 'transmission_spectrum'
            if len(xml_node_list) > 1:
                nm += '_' + str(i)
            if nm in nx_parent:
                print nm, ' already used!'
            nxdata = eznx.makeGroup(nx_parent, 
                                    utils.clean_name(nm), 'NXdata',
                                    canSAS_class='SAStransmission_spectrum',
                                    )
            nm = sas_ts.attrib.get('name')
            if nm is not None:
                eznx.addAttributes(nxdata, name=nm)
            nx_node_list.append(nxdata)

            # collect the data arrays
            data = {}
            units = {}
            for xmlnode in sas_ts:
                try:
                    if xmlnode.tag.endswith('}Tdata'):
                        for xmldata in xmlnode:
                            try:
                                tag = xmldata.tag.split('}')[-1]
                            except AttributeError, _exc:
                                continue        # an XML comment triggered this
                            if tag not in data:
                                data[tag] = []
                                units[tag] = xmldata.get('unit', 'none')
                            data[tag].append(xmldata.text)
                    else:
                        self.process_unexpected_xml_element(xmlnode, nxdata)
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
            if 'T' in data:
                eznx.addAttributes(nxdata, signal='T')
                if 'Lambda' in data:
                    eznx.addAttributes(nxdata, T_axes='Lambda')        # NeXus
                if 'Tdev' in data:
                    eznx.addAttributes(nxdata, T_uncertainty='Tdev')        # canSAS
                    eznx.addAttributes(nx_obj['T'], uncertainty='Tdev')     # NeXus

        return nx_node_list

    def process_SASsample(self, xml_parent, nx_parent):
        '''
        process the SASsample group, should be ONLY one
        '''
        nxsample = eznx.makeGroup(nx_parent, 
                                    'sassample', 'NXsample',
                                    canSAS_class='SASsample',
                                    )
        self.copy_attributes(xml_parent, nx_parent)
        
        details = []
        for xmlnode in xml_parent:
            if xmlnode.tag.endswith('}ID'):
                if xmlnode.text is None:
                    text = ''
                else:
                    text = xmlnode.text.strip()
                eznx.makeDataset(nxsample, 'ID', text)
            elif xmlnode.tag.endswith('}details'):
                details.append(xmlnode.text)
            elif xmlnode.tag.endswith('}orientation'):
                for xml_axis_node in xmlnode:
                    axis_name = xml_axis_node.tag.split('}')[-1]
                    axis_value = float(xml_axis_node.text)
                    axis_units = xml_axis_node.attrib.get('unit', 'unknown')
                    nxpos = eznx.makeGroup(nxsample, axis_name, 'NXposition')
                    eznx.makeDataset(nxpos, 'value', axis_value, units=axis_units)
                    description = 'rotation about the '
                    description += dict(roll='z', pitch='x', yaw='y')[axis_name]
                    description += ' axis'
                    eznx.makeDataset(nxpos, 'description', description)
            elif xmlnode.tag.endswith('}position'):
                for xml_axis_node in xmlnode:
                    axis_name = xml_axis_node.tag.split('}')[-1]
                    axis_value = float(xml_axis_node.text)
                    axis_units = xml_axis_node.attrib.get('unit', 'unknown')
                    nxpos = eznx.makeGroup(nxsample, axis_name, 'NXposition')
                    eznx.makeDataset(nxpos, 'value', axis_value, units=axis_units)
                    description = 'translation along the ' + axis_name + ' axis'
                    eznx.makeDataset(nxpos, 'description', description)
            elif xmlnode.tag.endswith('}thickness'):
                eznx.makeDataset(nxsample, 
                                 'thickness', 
                                 float(xmlnode.text),
                                 units=xmlnode.attrib.get('unit', 'none'))
            elif xmlnode.tag.endswith('}transmission'):
                eznx.makeDataset(nxsample, 
                                 'transmission', 
                                 float(xmlnode.text),
                                 units=xmlnode.attrib.get('unit', 'dimensionless'))
            elif xmlnode.tag.endswith('}temperature'):
                eznx.makeDataset(nxsample, 
                                 'temperature', 
                                 float(xmlnode.text),
                                 units=xmlnode.attrib.get('unit', 'unknown'))
            else:
                self.process_unexpected_xml_element(xmlnode, nxsample)
        
        if len(details) > 0:
            eznx.makeDataset(nxsample, 'details', '\n'.join(details))

    def process_unexpected_xml_element(self, xml_parent, nx_parent):
        '''
        process any unexpected XML element
        '''
        # TODO: is it a group or a field?  Assume field, at first.  
        # Expected coverage>90% of usage.  This will eventually fail.
        # BUT, need examples to show usage that to be handled.
        # If it is a group, it should be in an NXnote
        _field_or_group_trigger_ = xml_parent.text
        # If _field_or_group_trigger_ is None, then xml_parent MUST be a group?
        # But what about complexContent?  (i.e. text content AND element content?
        ns, nm = xml_parent.tag[1:].split('}')
        ds = eznx.makeDataset(nx_parent, nm, xml_parent.text, xml_namespace=ns)
        self.copy_attributes(xml_parent, nx_parent)
    
    def copy_attributes(self, xml_parent, nx_parent):
        '''
        copy any XML attributes to the HDF5 object
        '''
        eznx.addAttributes(nx_parent, **{k: v for k, v in xml_parent.attrib.items()})


def developer():
    from spec2nexus import h5toText
    filelist = '''
    bimodal-test1.xml
    s81-polyurea.xml
    1998spheres.xml
    '''.strip().split()
    filelist = os.listdir(os.path.join('..', 'xml'))    # TODO: what about .XML?
    # filelist = '''
    # GLASSYC_C4G8G9_w_TL.xml
    # samdata_WITHTX.xml
    # '''.strip().split()
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
