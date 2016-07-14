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
    
    def __str__(self, *args, **kwargs):
        if self.xmlFile is None:
            return object.__str__(self, *args, **kwargs)
        else:
            return self.xmlFile
    
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
        xml_node_list = xml_parent.findall('cs:SASentry', self.ns)
        for i, sasentry in enumerate(xml_node_list):
            nm = 'sasentry'
            if len(xml_node_list) > 1:
                nm += '_' + str(i)
            nm = sasentry.attrib.get('name', nm)
            nxentry = eznx.makeGroup(nx_parent, 
                                        utils.clean_name(nm), 
                                        'NXentry',
                                        canSAS_class='SASentry',
                                        canSAS_name=nm)
            nx_node_list.append(nxentry)
            eznx.makeDataset(nxentry, 'definition', 'NXcanSAS')

            # process the groups that may appear more than once
            group_list = self.process_SASdata(sasentry, nxentry)
            if len(group_list) > 0:
                default = group_list[0].name.split('/')[-1]
                eznx.addAttributes(nxentry, default=default)

            self.process_Run(sasentry, nxentry)
            self.process_SAStransmission_spectrum(sasentry, nxentry)
            self.process_SASprocess(sasentry, nxentry)
            self.process_SASnote(sasentry, nxentry)
            
            # process any other items
            for xmlnode in sasentry:
                if xmlnode.tag.endswith('}Title'):
                    self.field_text(xmlnode, nxentry, node_name='title')
                elif xmlnode.tag.endswith('}Run'):
                    pass            # handled above
                elif xmlnode.tag.endswith('}SASdata'):
                    pass            # handled above
                elif xmlnode.tag.endswith('}SASsample'):
                    self.process_SASsample(xmlnode, nxentry)
                elif xmlnode.tag.endswith('}SASinstrument'):
                    self.process_SASinstrument(xmlnode, nxentry)
                elif xmlnode.tag.endswith('}SASprocess'):
                    pass            # handled above
                elif xmlnode.tag.endswith('}SASnote'):
                    pass            # handled above
                elif xmlnode.tag.endswith('}SAStransmission_spectrum'):
                    pass            # handled above
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
            if len(xml_node_list) > 1:
                nm += '_' + str(i)
            ds = eznx.makeDataset(nx_parent, nm, xmlnode.text)
            self.copy_attributes(xml_parent, ds)

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
                                    utils.clean_name(nm), 
                                    'NXdata',
                                    canSAS_class='SASdata',
                                    canSAS_name=nm)
            nx_node_list.append(nxdata)
            
            # collect the SAS data arrays
            data = {}
            units = {}
            for xmlnode in sasdata:
                if isinstance(xmlnode.tag, str):    # avoid XML Comments
                    if xmlnode.tag.endswith('}Idata'):
                        for xmldata in xmlnode:
                            if isinstance(xmldata.tag, str):
                                tag = ns_strip(xmldata)
                                if tag not in data:
                                    data[tag] = []
                                    units[tag] = xmldata.get('unit', 'none')
                                data[tag].append(xmldata.text)
                    else:
                        self.process_unexpected_xml_element(xmlnode, nxdata)
            
            # write the data arrays
            nx_obj = {}
            for nm, arr in data.items():
                try:
                    nx_obj[nm] = eznx.makeDataset(nxdata, 
                                                  nm, 
                                                  map(float, data[nm]), 
                                                  units=units[nm])
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
                if 'Qdev' in data:
                    eznx.addAttributes(nx_obj['Q'], uncertainty='Qdev')     # NeXus
                if 'dQw' in data and 'dQl' in data: # not a common occurrence
                    # consider: Qdev or dQw & dQl
                    # http://cansas-org.github.io/canSAS2012/notation.html?highlight=uncertainty
                    # ----------------------------------
                    # skip this code, it is awkward and misleading
                    # instead, leave dQw & dQl where they are and do not set "Q/@uncertainty attribute
                    if False:
                        eznx.makeDataset(nx_components, 
                                                      'description', 
                                                      'both dQw and dQl contribute to the Q uncertainty')
                        if 'Qdev' in data:  # not very likely, the canSAS1d rules say no to this option
                            ref = nx_obj['Qdev']
                            del nx_obj['dQw']       # how to *move* instead?
                            nx_obj['dQw'] = eznx.makeDataset(nx_components, 
                                                      'dQw', 
                                                      map(float, data['dQw']), 
                                                      units=units['dQw'])
                        else:
                            # choose dQw or dQl at the top level
                            # move the other to the "Q_uncertainties" subgroup
                            ref = nx_obj['dQw']
                        del nx_obj['dQl']           # how to *move* instead?
                        nx_obj['dQl'] = eznx.makeDataset(nx_components, 
                                                  'dQl', 
                                                  map(float, data['dQl']), 
                                                  units=units['dQl'],
                                                  basis='as-reported',
                                                  used_with=nx_obj['dQw'].name)
                        eznx.addAttributes(ref, components='Q_uncertainties')     # NeXus
                        eznx.addAttributes(nx_obj['dQw'],                         # canSAS
                                           basis='as-reported',
                                           used_with=nx_obj['dQl'].name)

        return nx_node_list

    def process_SAStransmission_spectrum(self, xml_parent, nx_parent):
        '''
        process any SAStransmission_spectrum groups
        
        These are handled similar to SASdata but with different nouns
        
        Shouldn't this be located (in NeXus) at /NXentry/NXsample/transmission?
        '''
        nx_node_list = []
        xml_node_list = xml_parent.findall('cs:SAStransmission_spectrum', self.ns)
        for i, sas_ts in enumerate(xml_node_list):
            nm = 'transmission_spectrum'
            if len(xml_node_list) > 1:
                nm += '_' + str(i)
            nxdata = eznx.makeGroup(nx_parent, 
                                    utils.clean_name(nm), 
                                    'NXdata',
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
                if isinstance(xmlnode.tag, str):    # avoid XML Comments
                    if xmlnode.tag.endswith('}Tdata'):
                        for xmldata in xmlnode:
                            try:
                                tag = ns_strip(xmldata)
                            except AttributeError, _exc:
                                continue        # an XML comment triggered this
                            if tag not in data:
                                data[tag] = []
                                units[tag] = xmldata.get('unit', 'none')
                            data[tag].append(xmldata.text)
                    else:
                        self.process_unexpected_xml_element(xmlnode, nxdata)
            
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
        nm = xml_parent.attrib.get('name', 'sassample')
        nxsample = eznx.makeGroup(nx_parent, 
                                    utils.clean_name(nm), 
                                    'NXsample',
                                    canSAS_class='SASsample',
                                    canSAS_name=nm
                                    )
        self.copy_attributes(xml_parent, nx_parent)
        
        details = []    # report all *details* in a single multi-line string
        for xmlnode in xml_parent:
            if xmlnode.tag.endswith('}ID'):
                if xmlnode.text is None:
                    text = ''
                else:
                    text = xmlnode.text.strip()
                eznx.makeDataset(nxsample, 'ID', text)
            elif xmlnode.tag.endswith('}thickness'):
                self.field_float(xmlnode, nxsample, default_units='none')
            elif xmlnode.tag.endswith('}transmission'):
                self.field_float(xmlnode, nxsample, default_units='dimensionless')
            elif xmlnode.tag.endswith('}temperature'):
                self.field_float(xmlnode, nxsample, default_units='unknown')
            elif xmlnode.tag.endswith('}position'):
                self.axis_values(xmlnode, nxsample, '%s_position')
            elif xmlnode.tag.endswith('}orientation'):
                self.axis_values(xmlnode, nxsample)
            elif xmlnode.tag.endswith('}details'):
                details.append(xmlnode.text)
            else:
                self.process_unexpected_xml_element(xmlnode, nxsample)
        
        if len(details) > 0:
            eznx.makeDataset(nxsample, 'details', '\n'.join(details))

    def process_SASinstrument(self, sasinstrument, nx_parent):
        '''
        process the SASinstrument group, should be ONLY one
        '''
        nm = sasinstrument.attrib.get('name', 'sasinstrument')
        nxinstrument = eznx.makeGroup(nx_parent, 
                                    utils.clean_name(nm), 
                                    'NXinstrument',
                                    canSAS_class='SASinstrument',
                                    canSAS_name=nm)
        
        # process the groups that may appear more than once
        self.process_SAScollimation(sasinstrument, nxinstrument)
        self.process_SASdetector(sasinstrument, nxinstrument)
        
        for xmlnode in sasinstrument:
            if xmlnode.tag.endswith('}name'):
                self.field_text(xmlnode, nxinstrument)
            elif xmlnode.tag.endswith('}SASsource'):
                self.process_SASsource(xmlnode, nxinstrument)
            elif xmlnode.tag.endswith('}SAScollimation'):
                pass        # handled above
            elif xmlnode.tag.endswith('}SASdetector'):
                pass        # handled above
            else:
                self.process_unexpected_xml_element(xmlnode, nxinstrument)

    def process_SASsource(self, sassource, nx_parent):
        '''
        process the SASsource group, should be ONLY one
        '''
        nm = sassource.attrib.get('name', 'sassource')
        nxsource = eznx.makeGroup(nx_parent, 
                                  utils.clean_name(nm), 
                                  'NXsource', 
                                  canSAS_class='SASsource',
                                  canSAS_name=nm)

        for xmlnode in sassource:
            if isinstance(xmlnode.tag, str):    # avoid XML Comments
                if xmlnode.tag.endswith('}radiation'):
                    self.field_text(xmlnode, nxsource)
                elif xmlnode.tag.endswith('}beam_size'):
                    for subnode in xmlnode:
                        nm = ns_strip(subnode).lower()
                        if nm not in ('x', 'y'):
                            msg = 'unexpected tag: ' + subnode.tag
                            msg += '\n in SASsource group in file: ' + self.xmlFile
                            raise ValueError(msg)
                        self.field_float(subnode, nxsource, node_name='beam_size_' + nm)
                elif xmlnode.tag.endswith('}beam_shape'):
                    self.field_text(xmlnode, nxsource)
                elif xmlnode.tag.endswith('}wavelength'):
                    self.field_float(xmlnode, nxsource, node_name='incident_wavelength')
                elif xmlnode.tag.endswith('}wavelength_min'):
                    self.field_float(xmlnode, nxsource)
                elif xmlnode.tag.endswith('}wavelength_max'):
                    self.field_float(xmlnode, nxsource)
                elif xmlnode.tag.endswith('}wavelength_spread'):
                    self.field_float(xmlnode, nxsource)
                else:
                    self.process_unexpected_xml_element(xmlnode, nxsource)

    def process_SAScollimation(self, xml_parent, nx_parent):
        '''
        process any SAScollimation groups
        
        Should these be NXslit instead?
        '''
        xml_node_list = xml_parent.findall('cs:SAScollimation', self.ns)
        for i, sas_group in enumerate(xml_node_list):
            if isinstance(sas_group.tag, str):    # avoid XML Comments
                nm = sas_group.attrib.get('name')
                if nm is None:
                    nm = 'sascollimation'
                    if len(xml_node_list) > 1:
                        nm += '_' + str(i)
                nxcoll = eznx.makeGroup(nx_parent, 
                                        utils.clean_name(nm), 
                                        'NXcollimator', 
                                        canSAS_class='SAScollimation',
                                        canSAS_name=nm)
                
                # note: canSAS aperture does not map well into NXcollimator
                # might be better under SASinstrument but this is the defined location
                self.process_aperture(sas_group, nxcoll)
                
                for xmlnode in sas_group:
                    if isinstance(xmlnode.tag, str):    # avoid XML Comments
                        if xmlnode.tag.endswith('}length'):
                            ds = self.field_float(xmlnode, nxcoll)
                            comment = 'Amount/length of collimation inserted (on a SANS instrument)'
                            eznx.addAttributes(ds, comment=comment)
                        elif xmlnode.tag.endswith('}aperture'):
                            pass    # handled above
                        else:
                            self.process_unexpected_xml_element(xmlnode, nxcoll)

    def process_SASdetector(self, xml_parent, nx_parent):
        '''
        process any SASdetector groups
        '''
        xml_node_list = xml_parent.findall('cs:SASdetector', self.ns)
        for i, sas_group in enumerate(xml_node_list):
            if isinstance(sas_group.tag, str):    # avoid XML Comments
                nm = sas_group.attrib.get('name')
                if nm is None:
                    nm = 'sasdetector'
                    if len(xml_node_list) > 1:
                        nm += '_' + str(i)
                nxdetector = eznx.makeGroup(nx_parent, 
                                        utils.clean_name(nm), 
                                        'NXdetector', 
                                        canSAS_class='SASdetector',
                                        canSAS_name=nm)

                for xmlnode in sas_group:
                    if isinstance(xmlnode.tag, str):    # avoid XML Comments
                        if xmlnode.tag.endswith('}name'):
                            eznx.makeDataset(nxdetector, 'name', (xmlnode.text or '').strip())
                        elif xmlnode.tag.endswith('}SDD'):
                            ds = self.field_float(xmlnode, nxdetector)
                            comment = 'Distance between sample and detector'
                            eznx.addAttributes(ds, comment=comment)
                        elif xmlnode.tag.endswith('}offset'):
                            self.axis_values(xmlnode, nxdetector, '%s_position')
                        elif xmlnode.tag.endswith('}orientation'):
                            self.axis_values(xmlnode, nxdetector)
                        elif xmlnode.tag.endswith('}beam_center'):
                            self.axis_values(xmlnode, nxdetector, 'beam_center_%s')
                        elif xmlnode.tag.endswith('}pixel_size'):
                            self.axis_values(xmlnode, nxdetector, '%s_pixel_size')
                        elif xmlnode.tag.endswith('}slit_length'):
                            ds = self.field_float(xmlnode, nxdetector)
                            comment = 'Slit length of the instrument for this detector, '
                            comment += 'expressed in the same units as Q'
                            eznx.addAttributes(ds, comment=comment)
                        else:
                            self.process_unexpected_xml_element(xmlnode, nxdetector)

    def process_aperture(self, xml_parent, nx_parent):
        '''
        process an aperture XML element
        '''
        # note: canSAS aperture does not map well into NXcollimator
        # could be NXpinhole, NXslit, or NXaperture
        xml_node_list = xml_parent.findall('cs:aperture', self.ns)
        for i, xml_group in enumerate(xml_node_list):
            if isinstance(xml_group.tag, str):    # avoid XML Comments
                nm = xml_group.attrib.get('name')
                if nm is None:
                    nm = 'aperture'
                    if len(xml_node_list) > 1:
                        nm += '_' + str(i)

                # treat ALL as generic NXaperture
                nxaperture = eznx.makeGroup(nx_parent, 
                                        utils.clean_name(nm), 
                                        'NXaperture', 
                                        canSAS_class='aperture',
                                        canSAS_name=nm)

                shape = xml_group.attrib.get('type', 'not specified')
                eznx.makeDataset(nxaperture, 'shape', shape)

                for xmlnode in xml_group:
                    if isinstance(xmlnode.tag, str):
                        if xmlnode.tag.endswith('}size'):
                            self.axis_values(xmlnode, nxaperture, '%s_gap')
                        elif xmlnode.tag.endswith('}distance'):
                            self.field_float(xmlnode, nxaperture)
                        else:
                            self.process_unexpected_xml_element(xmlnode, nxaperture)

    def process_SASprocess(self, xml_parent, nx_parent):
        '''
        process any SASprocess groups
        '''
        xml_node_list = xml_parent.findall('cs:SASprocess', self.ns)
        for i, xml_group in enumerate(xml_node_list):
            nm = 'sasprocess'
            if len(xml_node_list) > 1:
                nm += '_' + str(i)
            nm = xml_group.attrib.get('name', nm)
            nxprocess = eznx.makeGroup(nx_parent, 
                                    utils.clean_name(nm), 
                                    'NXprocess',
                                    canSAS_class='SASprocess',
                                    canSAS_name=nm)

            term_counter = 0
            for xmlnode in xml_group:
                if isinstance(xmlnode.tag, str):
                    if xmlnode.tag.endswith('}name'):
                        self.field_text(xmlnode, nxprocess)
                    elif xmlnode.tag.endswith('}date'):
                        # TODO: test for ISO-8601?
                        # need to convert from arbitrary representations
                        # 01-DEC-2008 04:30:25
                        # 1-Jul-1998 14:57:37
                        # 04-Sep-2007 18:12:27
                        # Tue, May 20, 2008  1:39:23 PM
                        # Tue, Aug 21, 2007
                        # 1999-01-04 20:15:45
                        # 1999-01-04T20:15:45
                        self.field_text(xmlnode, nxprocess)
                    elif xmlnode.tag.endswith('}description'):
                        self.field_text(xmlnode, nxprocess)
                    elif xmlnode.tag.endswith('}term'):
                        nm = 'term_'+str(term_counter)
                        term_counter += 1
                        ds = self.field_text(xmlnode, nxprocess, node_name=nm)
                        self.copy_attributes(xmlnode, ds)
                        units = xmlnode.attrib.get('unit')
                        if units is not None:
                            eznx.addAttributes(ds, units=units)
                            del ds.attrs['unit']    # remove the canSAS singular name
                    elif xmlnode.tag.endswith('}SASprocessnote'):
                        pass    # handled below
                    else:
                        self.process_unexpected_xml_element(xmlnode, nxprocess)
            
            self.process_SASprocessnote(xml_group, nxprocess)

    def process_SASprocessnote(self, xml_parent, nx_parent):
        '''
        process any SASprocessnote groups
        '''
        xml_node_list = xml_parent.findall('cs:SASprocessnote', self.ns)
        for i, xml_group in enumerate(xml_node_list):
            nm = 'sasprocessnote'
            if len(xml_node_list) > 1:
                nm += '_' + str(i)
            nm = xml_group.attrib.get('name', nm)
            nxprocessnote = eznx.makeGroup(nx_parent, 
                                    utils.clean_name(nm), 
                                    'NXnote',
                                    canSAS_class='SASprocessnote',
                                    canSAS_name=nm)

            self.copy_attributes(xml_group, nxprocessnote)
            
            self.process_collection_group(xml_group, nxprocessnote)

    def process_SASnote(self, xml_parent, nx_parent):
        '''
        process any SASnote groups
        '''
        xml_node_list = xml_parent.findall('cs:SASnote', self.ns)
        for i, xml_group in enumerate(xml_node_list):
            nm = 'sasnote'
            if len(xml_node_list) > 1:
                nm += '_' + str(i)
            nm = xml_group.attrib.get('name', nm)
            nxnote = eznx.makeGroup(nx_parent, 
                                    utils.clean_name(nm), 
                                    'NXnote',
                                    canSAS_class='SASnote',
                                    canSAS_name=nm)
            
            self.process_collection_group(xml_group, nxnote)

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

        ns, nm = ns_split(xml_parent)
        ds = eznx.makeDataset(nx_parent, nm, xml_parent.text, xml_namespace=ns)
        self.copy_attributes(xml_parent, nx_parent)
    
    def copy_attributes(self, xml_parent, nx_parent):
        '''
        copy any XML attributes to the HDF5 object
        '''
        eznx.addAttributes(nx_parent, **{k: v for k, v in xml_parent.attrib.items()})
    
    def field_text(self, xmlnode, nx_parent, node_name=None):
        '''
        get the text from xmlnode and write it to nxparent
        '''
        nm = node_name or ns_strip(xmlnode)
        if nm not in nx_parent:
            ds = eznx.makeDataset(nx_parent, nm, (xmlnode.text or '').strip())
            return ds
    
    def field_float(self, xmlnode, nx_parent, node_name=None, default_units='unknown'):
        '''
        get a float value from xmlnode and write it to nxparent
        '''
        nm = node_name or ns_strip(xmlnode)
        units = xmlnode.attrib.get('unit', default_units)
        ds = eznx.makeDataset(nx_parent, 
                    nm, 
                    float(xmlnode.text),
                    units=units)
        return ds

    def axis_values(self, xml_parent, nx_parent, template='%s'):
        '''
        copy a set of x,y,z (or roll,pitch,yaw) as floats to nx_parent
        '''
        #rotations = dict(roll='z', pitch='x', yaw='y')
        rotations = dict(roll='polar_angle', pitch='x_axis_rotation', yaw='azimuthal_angle')
        for axisnode in xml_parent:
            if isinstance(axisnode.tag, str):
                nm = ns_strip(axisnode)
                if nm in rotations:
                    nm = rotations[nm]  # name substitution for roll, pitch, and yaw
                else:
                    nm = template % nm
                self.field_float(axisnode, nx_parent, node_name=nm)

    def process_collection_group(self, xml_parent, nx_parent):
        '''
        process any collection group XML element

        In NXcollection, the content does not have to be NeXus.
        Could use plain hdf5 groups and datasets, both with attributes.
        But, it's more consistent to stay in NeXus structures,
        so nest NXcollections.
        '''
        if len(xml_parent) == 0: # just a text field, don't assume it is a number
            tag = ns_strip(xml_parent)
            nm = self.unique_hdf5_name(nx_parent, xml_parent, tag)
            ds = self.field_text(xml_parent, nx_parent, node_name=nm)
            if ds is not None:
                eznx.addAttributes(ds, tag = tag)
                self.copy_attributes(xml_parent, nx_parent)
        else:
            for xmlnode in xml_parent:
                if len(xmlnode) == 0:
                    self.process_collection_group(xmlnode, nx_parent)
                else:
                    tag = ns_strip(xmlnode)
                    nm = xmlnode.attrib.get('name', tag)
                    nm = self.unique_hdf5_name(nx_parent, xmlnode, nm)
                    nxgroup = eznx.makeGroup(nx_parent, 
                                            utils.clean_name(nm), 
                                            'NXcollection',
                                            canSAS_name=nm)
                    self.copy_attributes(xmlnode, nxgroup)
                    eznx.addAttributes(nxgroup, tag=tag)
                    self.process_collection_group(xmlnode, nxgroup)
    
    def unique_hdf5_name(self, nx_parent, xml_node, suggested_name):
        '''
        ensure a unique HDF5 name is chosen for use in the nx_parent group
        '''
        nm = suggested_name
        same_node_count = len(xml_node.getparent().findall('cs:'+suggested_name, self.ns))
        if same_node_count > 1: # all names in an HDF5 group must be unique
            for i in range(same_node_count):
                nm = suggested_name + '_' + str(i)
                if nm not in nx_parent: # find a unique name
                    break
        return nm


def ns_split(xmlnode):
    '''
    split text into full XML namespace and tag
    '''
    return xmlnode.tag[1:].split('}')


def ns_strip(xmlnode):
    '''
    return XML tag from xmlnode without XML namespace
    '''
    return ns_split(xmlnode)[-1]


def developer():
    from spec2nexus import h5toText
    filelist = os.listdir(os.path.join('..', 'xml'))
    for fname in filelist:
        if fname.find('cansas1d-template.xml') >= 0:
            continue
        if fname.find('cansas1d.xml') >= 0:
            continue
        if fname.lower().endswith('.xml'):
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
    simple command line interface
    '''
    if len(sys.argv) == 1:
        print 'usage: xml2hdf5 xmlfile [xmlfile [xmlfile [...]]]'
    else:
        for xmlFile in sys.argv[1:]:
            converter = canSAS1D_to_NXcanSAS()
            converter.open_XML(xmlFile)
            hdf5File = os.path.splitext(xmlFile)[0] + '.h5'
            converter.write_HDF5(hdf5File)


if __name__ == "__main__":
    #developer()
    main()
