#!/usr/bin/env python

'''Extended example use of cansas1d reader'''

# Copyright (c) 2013, UChicago Argonne, LLC
# This file is distributed subject to a Software License Agreement found
# in the file LICENSE that is included with this distribution. 


import os
import sys
import cansas1d

__svn_id__ = "$Id$"



def indra_metadata(SASentry):
    '''print metadata from APS/USAXS Indra package'''
    if 'metadata' in SASentry.__dict__:
        for metadata in SASentry.metadata:
            '''loop through the USAXS metadata'''
            print metadata.xmlns
            for index in metadata.usaxs:
                '''multiple invocations of the usaxs element'''
                for item in dir(index):
                    '''discover the element names'''
                    if item[0] == '_':    # sift out data structure management terms
                        continue
                    if item in ('PCDATA', 'name', 'xmlns'):  # sift this out
                        continue
                    s = ''
                    s += '('+index.xmlns+') '
                    s += '('+index.name+') '
                    s += item + ': '
                    s += index.__dict__[item].PCDATA
                    print s


def print_SASdata(sd):
    '''print the contents of the SASdata element'''
    numPts = len(sd.Idata)
    if 'name' in sd.__dict__:
        print 'SASdata name:', sd.name
    print '# points:', numPts
    columns = [
        ['Q ('+sd.Idata[0].Q.unit+')'],
        ['I ('+sd.Idata[0].I.unit+')'],
        ['Idev ('+sd.Idata[0].Idev.unit+')'],
    ]
    for Idata in sd.Idata:
        values = (Idata.Q.PCDATA, Idata.I.PCDATA, Idata.Idev.PCDATA)
        for item, value in enumerate(values):
            columns[item].append(str(value))
    print columnsToText(columns)


def print_optional_item(title, parent, item):
    ''' this item is optional and may not be present'''
    if item in parent.__dict__:
        #print item, item in parent.__dict__
        obj = parent.__dict__[item]
        s = title+':\t'
        s += obj.PCDATA
        if 'unit' in obj.__dict__:
            s += ' (' + obj.unit + ')'
        print s


def columnsToText(columns):
    '''
    convert a list of column lists into rows of text
    
    column widths will be chosen from the maximum character width of each column
    
    :param [[str]] columns: list of column lists (all same length)
    :returns str: text block, with line separators
    
    Example::
    
        >>> columns = [ ['1A', '2A'], ['1B is long', '2B'], ['1C', '2C'] ]
        >>> print columnsToText( columns )
        1A  1B is long  1C
        2A  2B          2C
    
    '''
    # get the largest width for each column
    widths = [max(map(len, item)) for item in columns]
    # left-align each column
    sep = ' '*2
    fmt = sep.join(['%%-%ds' % item for item in widths])
    # rows = zip(*columns) : matrix transpose
    result = [fmt % tuple(row) for row in zip(*columns)]
    return '\n'.join(result)


def demo(xmlFile):
    print '#---------------------------------------------------'
    print 'XML:', xmlFile
    # read in the XML file
    try:
        sasxml = cansas1d.readCanSasFile(xmlFile)
    except cansas1d.Exception_canSAS_namespace, answer:
        print "wrong XML namespace:", answer
        return
    except cansas1d.Exception_canSAS_version, answer:
        print "wrong version string:", answer
        return
    print 'namespace:', sasxml.xmlns
    print 'version:', sasxml.version
    SASentry = sasxml.SASentry                  # just the first one
    print 'title:', SASentry.Title.PCDATA
    print 'run:', SASentry.Run.PCDATA
    print_optional_item('instrument', SASentry.SASinstrument, 'name')
    indra_metadata(SASentry)        # foreign XML elements from APS/USAXS
    print_optional_item('sample ID', SASentry.SASsample, 'ID')
    print_optional_item('sample thickness', SASentry.SASsample, 'thickness')
    print_optional_item('sample transmission', SASentry.SASsample, 'transmission')
    if 'position' in SASentry.SASsample.__dict__:
        print_optional_item('sample X', SASentry.SASsample.position, 'x')
        print_optional_item('sample Y', SASentry.SASsample.position, 'y')
    print_SASdata(SASentry.SASdata)


if __name__ == "__main__":
    if len(sys.argv) == 2:
        demo(sys.argv[1])
    else:
        demo(os.path.join('..', 'examples', 'bimodal-test1.xml'))
        demo(os.path.join('..', 'examples', 's81-polyurea.xml'))
