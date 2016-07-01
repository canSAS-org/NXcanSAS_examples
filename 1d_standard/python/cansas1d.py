#!/usr/bin/env python

''' 
read canSAS 1-D XML data files (either v1.0 or v1.1)

:requires: 
    gnosis.xml.objectify     # easy_install -U gnosis

basic use in a program::

    import cansas1d
    try:
        sasxml = cansas1d.readCanSasFile(xmlFile)
    except cansas1d.Exception_canSAS_namespace, answer:
        print "wrong XML namespace:", answer
        return
    except cansas1d.Exception_canSAS_version, answer:
        print "wrong version string:", answer
        return

Copyright (c) 2013, UChicago Argonne, LLC
This file is distributed subject to a Software License Agreement found
in the file LICENSE that is included with this distribution. 
'''


import os
import sys
import gnosis.xml.objectify     # easy_install -U gnosis


    # support reading v1.0 and v1.1 data files
    # v1.1 schema is backwards compatible, mostly
CANSAS_NAMESPACES = {
    '1.0': 'cansas1d/1.0',
    '1.1': 'urn:cansas1d:1.1',
}


def readCanSasFile(xmlFile):
    '''
    open a canSAS XML data file as a gnosis file object
    
    :param str xmlFile: name of canSAS 1D XML data file
    :returns: gnosis object with XML data structure
    :raises Exception_canSAS_namespace: if namespace does not match
    :raises Exception_canSAS_version: if version does not match
    '''
    # read in the XML file
    sasxml = gnosis.xml.objectify.XML_Objectify(xmlFile).make_instance()
    
    # namespace check to accept file as canSAS XML
    if sasxml.xmlns not in CANSAS_NAMESPACES.values():
        raise Exception_canSAS_namespace, str(sasxml.xmlns)
    
    # version check
    if sasxml.version not in CANSAS_NAMESPACES.keys():
        raise Exception_canSAS_version, str(sasxml.version)
    
    return sasxml

class Exception_canSAS_namespace(Exception):
    '''canSAS XML file namespace'''

class Exception_canSAS_version(Exception):
    '''version string of the canSAS standard'''

if __name__ == "__main__":
    '''just for demonstration using example data files'''
    for xmlFile in ('bimodal-test1', 's81-polyurea'):
        path = os.path.abspath(os.path.join('..', 'examples', xmlFile+'.xml'))
        if not os.path.exists(path):
            continue
        try:
            sasxml = readCanSasFile(path)
        except Exception_canSAS_namespace, answer:
            print xmlFile, "wrong XML namespace:", answer
            continue
        except Exception_canSAS_version, answer:
            print xmlFile, "wrong version string:", answer
            continue
        print '%s has %d data points' % (xmlFile, len(sasxml.SASentry.SASdata.Idata))
        
