#!/usr/bin/env python

'''
Create HDF5 example files in the NXcanSAS format

These examples are based on the examples described at the canSAS2012 meeting.

:see: http://cansas-org.github.io/canSAS2012/examples.html
'''

import datetime
import h5py
import inspect
import numpy
import os
import sys


def basic_setup(filename):
    '''
    Create the HDF5 file and basic structure, return the nxdata object
    
    structural model::

        SASroot
          SASentry
            SASdata

    COMMENTS:
    
    Various metadata are added to the NXroot group (as attributes).
    These are optional but help define the history of each file.
    
    The "default" attribute supports the NeXus motivation to easily 
    identify the data to be use for a default visualization of this file.
    The value is the name of the child group on the path to this data.
    The path defined by canSAS is "/sasentry/sasdata/I".
    
    In the file root (SASroot/NXroot) group, default="sasentry".
    In the entry (SASentry/NXentry) group, default="sasdata".
    In the data (SASdata/NXdata) group, signal="I".
    
    In the data group, the "axes" attribute associates the Q dataset
    with the signal="I" dataset.  It may be changed as needed by the 
    situation, such as for Qx, Qy.
    
    To preserve the mapping between canSAS and NeXus structures,
    additional canSAS attributes are added.  These are permitted and 
    ignored by NeXus.
    
    The arrays in these examples are small, when compared with
    many real-world datasets but are intended to demonstrate the
    use of the format while reducing the file size of the example.
    
    A "units" attribute is recommended for all numerical datasets (fields).
    '''
    nxroot = h5py.File(filename, "w")
    nxroot.attrs['file_name'] = filename
    nxroot.attrs['HDF5_Version'] = h5py.version.hdf5_version
    nxroot.attrs['h5py_version'] = h5py.version.version
    nxroot.attrs['file_time'] = str(datetime.datetime.now())
    nxroot.attrs['producer'] = __file__  # os.path.abspath(__file__)
    nxroot.attrs['default'] = "sasentry"

    nxentry = nxroot.create_group("sasentry")
    nxentry.attrs["NX_class"] = "NXentry"
    nxentry.attrs["SAS_class"] = "SASentry"
    nxentry.attrs['default'] = "sasdata"
    nxentry.create_dataset("definition", data="NXcanSAS")

    nxdata = nxentry.create_group("sasdata")
    nxdata.attrs["NX_class"] = "NXdata"
    nxdata.attrs["SAS_class"] = "SASdata"
    nxdata.attrs["signal"] = "I"
    nxdata.attrs["axes"] = "Q" 
       
    return nxdata


def fake_data(*dimensions):
    '''
    create a dataset array from random numbers with the supplied dimension(s)
    
    Examples:
    
    :1D: ``fake_data(5)``
    :2D: ``fake_data(5, 10)``
    :2D image: ``fake_data(10, 50)``
    :3D (3 2D images): ``fake_data(3, 10, 50)``
    
    Use a random number generator.  
    There is no science to be interpreted from the values.
    
    Use of "*dimensions" allows this routine to be called with arbitrary
    array shape.
    '''
    return numpy.random.rand(*dimensions)


def get_method_name():
    '''
    return the name of the method from which this method has been called
    '''
    stack = inspect.stack()
    mname = stack[1][3]
    return mname


def example_01_1D_I_Q():
    '''
    The most common SAS data is I(|Q|), a one-dimensional set of data.
    
    structural model::
    
        SASroot
          SASentry
            SASdata
              I: float[10]
              Q: float[10]

    '''
    nxdata = basic_setup(get_method_name() + ".h5")
    nxdata.attrs["Q_indices"] = 0

    n = 10
    ds = nxdata.create_dataset("I", data=fake_data(n))
    ds.attrs["units"] = "1/m"
    ds = nxdata.create_dataset("Q", data=fake_data(n))
    ds.attrs["units"] = "1/nm"

    nxdata.file.close()


def example_02_2D_image():
    '''
    Analysis of 2-D images is common
    
    The "Q_indices" attribute indicates the dependency relationship 
    of the Q field with one or more dimensions of the plottable "I" data.
    This is an integer array that defines the indices of the "I" field 
    which need to be used in the "Q" dataset in order to reference the 
    corresponding axis value.    This 2D example is a good demonstration 
    of this feature.

    structural model::

        SASroot
          SASentry
            SASdata
              I: float[10, 50]
              Q: float[10, 50]

    '''
    nxdata = basic_setup(get_method_name() + ".h5")
    nxdata.attrs["axes"] = ["Q", "Q"]
    nxdata.attrs["Q_indices"] = [0, 1]

    h = 10
    v = 50
    ds = nxdata.create_dataset("I", data=fake_data(h, v))
    ds.attrs["units"] = "1/m"
    ds = nxdata.create_dataset("Q", data=fake_data(h, v))
    ds.attrs["units"] = "1/nm"

    nxdata.file.close()


def example_03_2D_image_and_uncertainties():
    '''
    Uncertainties (a.k.a "errors") may be identified.

    The mechanism is to provide a dataset of the same shape as "I",
    and identify its name in the "uncertainties" attribute.
    Note in NeXus, this attribute is spelled as a plural, not "uncertainty".
    The value is the name of the dataset with the uncertainties.
    
    The name "Idev" is preferred by canSAS for the uncertainty of "I".
    
    This technique to identify uncertainties can be applied to
    any dataset.  It is up to each analysis procedure to recognize
    and handle this information.

    structural model::

        SASroot
          SASentry
            SASdata
              I: float[10, 50]
                @uncertainties=Idev
              Q: float[10, 50]
              Idev: float[10, 50]

    '''
    nxdata = basic_setup(get_method_name() + ".h5")
    nxdata.attrs["axes"] = "Q Q".strip()        # same as ["Q", "Q"]
    nxdata.attrs["Q_indices"] = [0, 1]

    h = 10
    v = 50
    ds = nxdata.create_dataset("I", data=fake_data(h, v))
    ds.attrs["units"] = "1/m"
    ds.attrs["uncertainties"] = "Idev"
    ds = nxdata.create_dataset("Q", data=fake_data(h, v))
    ds.attrs["units"] = "1/nm"
    ds = nxdata.create_dataset("Idev", data=fake_data(h, v))
    ds.attrs["units"] = "1/m"

    nxdata.file.close()


def example_04_2D_vector():
    '''
    Q may be represented as a vector
    
    The canSAS interpretation of the "axes" attribute differs from NeXus.
    In canSAS, "Q" when used as a vector is recognized as a value of the
    "axess" attrribute.  NeXus requires *each* value in the "axes" attribute
    list must exist as a dataset in the same group.

    structural model::

        SASroot
          SASentry
            SASdata
              I: float[10, 50]
              Qx: float[10, 50]
              Qy: float[10, 50]
              Qz: float[10, 50]

    '''
    nxdata = basic_setup(get_method_name() + ".h5")
    nxdata.attrs["axes"] = "Qx Qy".strip()
    nxdata.attrs["Qx_indices"] = 0
    nxdata.attrs["Qy_indices"] = 1

    h = 10
    v = 50
    ds = nxdata.create_dataset("I", data=fake_data(h, v))
    ds.attrs["units"] = "1/m"
    ds = nxdata.create_dataset("Qx", data=fake_data(h, v))
    ds.attrs["units"] = "1/nm"
    ds = nxdata.create_dataset("Qy", data=fake_data(h, v))
    ds.attrs["units"] = "1/nm"
    ds = nxdata.create_dataset("Qz", data=0*fake_data(h, v))
    ds.attrs["units"] = "1/nm"

    nxdata.file.close()


def example_05_2D_SAS_WAS():
    '''
    common multi-method technique: small and wide angle scattering
    
    WAS is not in the scope of the NXcanSAS definition.
    Still, it is useful to demonstrate how WAS might be included in
    a NXcanSAS data file, in a NXdata group.

    structural model::

    SASroot
      SASentry
        SASdata
          @name="sasdata"
          I: float[10, 50]
          Q: float[10, 50]
        SASdata
          @name="wasdata"
          I: float[25, 25]
          Q: float[25, 25]

    '''
    nxdata = basic_setup(get_method_name() + ".h5")
    nxdata.attrs["axes"] = "Q Q".strip()
    nxdata.attrs["Q_indices"] = [0, 1]

    # SAS data
    h = 10
    v = 50
    ds = nxdata.create_dataset("I", data=fake_data(h, v))
    ds.attrs["units"] = "1/m"
    ds = nxdata.create_dataset("Q", data=fake_data(h, v))
    ds.attrs["units"] = "1/nm"

    nxentry = nxdata.parent

    # WAS data
    was_group = nxentry.create_group("wasdata")
    was_group.attrs["NX_class"] = "NXdata"
    was_group.attrs["signal"] = "I"
    was_group.attrs["axes"] = "Q Q".strip()
    was_group.attrs["Q_indices"] = [0, 1]

    h = 25
    v = 25
    ds = was_group.create_dataset("I", data=fake_data(h, v))
    ds.attrs["units"] = "1/m"
    ds = was_group.create_dataset("Q", data=fake_data(h, v))
    ds.attrs["units"] = "1/nm"

    nxdata.file.close()


def example_06_2D_Masked():
    '''
    Data masks are possible in analysis of SAS
    
    NeXus has defined a 32-bit integer "pixel_mask" field to describe
    various possible reasons for masking a specific pixel, as a bit map.
    The same definition is used in two NeXus classes.  
    See either NXdetector base class or NXmx application definition for details.
    
    Here, the random data only uses a value of 0 (no mask) or 1 (dead pixel).

    structural model::

        SASroot
          SASentry
            SASdata
              I: float[10, 50]
              Q: float[10, 50]
              Mask: int[10, 50]

    '''
    nxdata = basic_setup(get_method_name() + ".h5")
    nxdata.attrs["axes"] = "Q Q".strip()
    nxdata.attrs["Q_indices"] = [0, 1]

    h = 10
    v = 50
    ds = nxdata.create_dataset("I", data=fake_data(h, v))
    ds.attrs["units"] = "1/m"
    ds = nxdata.create_dataset("Q", data=fake_data(h, v))
    ds.attrs["units"] = "1/nm"
    mask_data = numpy.int32(numpy.random.rand(h, v) + 0.5)
    ds = nxdata.create_dataset("Mask", data=mask_data)

    nxdata.file.close()


def example_07_2D_as_1D():
    '''
    Mapping of 2D data into 1D is common
    
    This is used to describe radial averaged I(Q) data.
    It may also be used to describe data combined from several measurements.

    structural model::

        SASroot
          SASentry
            SASdata
              I: float[10*50]
              Q: float[10*50]

    '''
    nxdata = basic_setup(get_method_name() + ".h5")
    nxdata.attrs["Q_indices"] = 0

    h = 10
    v = 50
    ds = nxdata.create_dataset("I", data=fake_data(h * v))
    ds.attrs["units"] = "1/m"
    ds = nxdata.create_dataset("Q", data=fake_data(h * v))
    ds.attrs["units"] = "1/nm"

    nxdata.file.close()


def example_08_SANS_SAXS():
    '''
    Complementary technique.
    
    This example shows where to place the I(Q) data.
    It could be improved by showing the placement of the additional
    data related to the wavelength of the radiation of each source.
    
    Both SANS and SAXS data belong in the same entry as they pertain 
    to the same sample.  A "probe_type" attribute has been added
    to each data group to further identify in a standard way,
    using nouns defined by NeXus.
    
    The selection of the "sans" group is arbitrary in this example.
    NeXus does not allow for multiple values in the "default" attribute.

    structural model::

        SASroot
          SASentry
            SASdata
              @name="sans"
              @probe_type="neutron"
              I: float[10]
              Q: float[10]
            SASdata
              @name="saxs"
              @probe_type="xray"
              I: float[25]
              Q: float[25]

    The example code below shows an h5py technique to rename the
    "sasdata" group to "sans".  This adds clarity to the example data file.
    '''
    nxdata = basic_setup(get_method_name() + ".h5")
    nxdata.attrs["probe_type"] = "neutron"
    nxdata.attrs["Q_indices"] = 0

    n = 10
    ds = nxdata.create_dataset("I", data=fake_data(n))
    ds.attrs["units"] = "1/m"
    ds = nxdata.create_dataset("Q", data=fake_data(n))
    ds.attrs["units"] = "1/nm"

    nxentry = nxdata.parent
    nxentry.attrs["default"] = "sans"
    nxentry["sans"] = nxdata            # change the nxdata group name
    del nxentry["sasdata"]

    nxdata = nxentry.create_group("saxs")
    nxdata.attrs["NX_class"] = "NXdata"
    nxdata.attrs["SAS_class"] = "SASdata"
    nxdata.attrs["probe_type"] = "xray"

    n = 25
    ds = nxdata.create_dataset("I", data=fake_data(n))
    ds.attrs["units"] = "1/m"
    ds = nxdata.create_dataset("Q", data=fake_data(n))
    ds.attrs["units"] = "1/nm"

    nxdata.file.close()


def example_09_1D_time():
    '''
    A time-series of 1D I(Q) data
    
    This is another example of how to apply the "AXISNAME_indices"
    attributes.  "Time" is used with the first index of "I",
    "Q" with the second.

    structural model::

        SASroot
          SASentry
            SASdata
              @axes=Time,Q
              @Time_indices=0
              @Q_indices=1
              Time: float[nTime]  
              Q: float[10]
              I: float[nTime,10]

    '''
    nxdata = basic_setup(get_method_name() + ".h5")
    nxdata.attrs["axes"] = "Time Q".split()
    nxdata.attrs["Time_indices"] = 0
    nxdata.attrs["Q_indices"] = 1

    n = 10
    nTime = 5
    ds = nxdata.create_dataset("I", data=fake_data(nTime, n))
    ds.attrs["units"] = "1/m"
    ds = nxdata.create_dataset("Q", data=fake_data(n))
    ds.attrs["units"] = "1/nm"
    ds = nxdata.create_dataset("Time", data=fake_data(nTime))
    ds.attrs["units"] = "s"

    nxdata.file.close()


if __name__ == "__main__":
    example_01_1D_I_Q()
    example_02_2D_image()
    example_03_2D_image_and_uncertainties()
    example_04_2D_vector()
    example_05_2D_SAS_WAS()
    example_06_2D_Masked()
    example_07_2D_as_1D()
    example_08_SANS_SAXS()
    example_09_1D_time()
