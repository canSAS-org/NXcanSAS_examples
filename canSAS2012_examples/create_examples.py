#!/usr/bin/env python

'''
Create HDF5 example files in the NXcanSAS format

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
    
    ::

        SASroot
          SASentry
            SASdata

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
    
    return nxdata


def fake_data(*dimensions):
    '''
    create a dataset from random numbers with the supplied dimension(s)
    
    Examples:
    
    :1D: ``fake_data(5)``
    :2D: ``fake_data(5, 10)``
    :2D image: ``fake_data(100, 512)``
    :3D (3 2D images): ``fake_data(3, 100, 512)``
    '''
    return numpy.random.rand(*dimensions)


def get_method_name():
    ''' '''
    stack = inspect.stack()
    mname = stack[1][3]
    return mname


def example_01_1D_I_Q():
    '''
    ::
    
        SASroot
          SASentry
            SASdata
              I: float[100]
              Q: float[100]

    '''
    nxdata = basic_setup(get_method_name() + ".h5")
    nxdata.attrs["signal"] = "I"
    nxdata.attrs["axes"] = "Q"
    nxdata.attrs["Q_indices"] = 0

    n = 100
    ds = nxdata.create_dataset("I", data=fake_data(n))
    ds.attrs["units"] = "1/cm"
    ds = nxdata.create_dataset("Q", data=fake_data(n))
    ds.attrs["units"] = "1/A"

    nxdata.file.close()


def example_02_2D_image():
    '''
    ::

        SASroot
          SASentry
            SASdata
              I: float[100, 512]
              Q: float[100, 512]

    '''
    nxdata = basic_setup(get_method_name() + ".h5")
    nxdata.attrs["signal"] = "I"
    nxdata.attrs["axes"] = ["Q", "Q"]
    nxdata.attrs["Q_indices"] = [0, 1]

    h = 100
    v = 512
    ds = nxdata.create_dataset("I", data=fake_data(h, v))
    ds.attrs["units"] = "1/cm"
    ds = nxdata.create_dataset("Q", data=fake_data(h, v))
    ds.attrs["units"] = "1/A"

    nxdata.file.close()


def example_03_2D_image_and_uncertainties():
    '''
    ::

        SASroot
          SASentry
            SASdata
              I: float[100, 512]
                @uncertainties=Idev
              Q: float[100, 512]
              Idev: float[100, 512]

    '''
    nxdata = basic_setup(get_method_name() + ".h5")
    nxdata.attrs["signal"] = "I"
    nxdata.attrs["axes"] = "Q Q".strip()        # same as ["Q", "Q"]
    nxdata.attrs["Q_indices"] = [0, 1]

    h = 100
    v = 512
    ds = nxdata.create_dataset("I", data=fake_data(h, v))
    ds.attrs["units"] = "1/cm"
    ds.attrs["uncertainties"] = "Idev"
    ds = nxdata.create_dataset("Q", data=fake_data(h, v))
    ds.attrs["units"] = "1/A"
    ds = nxdata.create_dataset("Idev", data=fake_data(h, v))
    ds.attrs["units"] = "1/cm"

    nxdata.file.close()


def example_04_2D_vector():
    '''
    ::

        SASroot
          SASentry
            SASdata
              I: float[100, 512]
              Qx: float[100, 512]
              Qy: float[100, 512]
              Qz: float[100, 512]

    '''
    nxdata = basic_setup(get_method_name() + ".h5")
    nxdata.attrs["signal"] = "I"
    nxdata.attrs["axes"] = "Qx Qy".strip()
    nxdata.attrs["Qx_indices"] = 0
    nxdata.attrs["Qy_indices"] = 1

    h = 100
    v = 512
    ds = nxdata.create_dataset("I", data=fake_data(h, v))
    ds.attrs["units"] = "1/cm"
    ds = nxdata.create_dataset("Qx", data=fake_data(h, v))
    ds.attrs["units"] = "1/A"
    ds = nxdata.create_dataset("Qy", data=fake_data(h, v))
    ds.attrs["units"] = "1/A"
    ds = nxdata.create_dataset("Qz", data=0*fake_data(h, v))
    ds.attrs["units"] = "1/A"

    nxdata.file.close()


def example_05_2D_SAS_WAS():
    '''
    ::

    SASroot
      SASentry
        SASdata
          @name="sasdata"
          I: float[100, 512]
          Q: float[100, 512]
        SASdata
          @name="wasdata"
          I: float[256, 256]
          Q: float[256, 256]

    '''
    nxdata = basic_setup(get_method_name() + ".h5")
    nxdata.attrs["signal"] = "I"
    nxdata.attrs["axes"] = "Q Q".strip()
    nxdata.attrs["Q_indices"] = [0, 1]

    # SAS data
    h = 100
    v = 512
    ds = nxdata.create_dataset("I", data=fake_data(h, v))
    ds.attrs["units"] = "1/cm"
    ds = nxdata.create_dataset("Q", data=fake_data(h, v))
    ds.attrs["units"] = "1/A"

    nxentry = nxdata.parent

    # WAS data
    was_group = nxentry.create_group("wasdata")
    was_group.attrs["NX_class"] = "NXdata"
    was_group.attrs["signal"] = "I"
    was_group.attrs["axes"] = "Q Q".strip()
    was_group.attrs["Q_indices"] = [0, 1]

    h = 256
    v = 256
    ds = was_group.create_dataset("I", data=fake_data(h, v))
    ds.attrs["units"] = "1/cm"
    ds = was_group.create_dataset("Q", data=fake_data(h, v))
    ds.attrs["units"] = "1/A"

    nxdata.file.close()


def example_06_2D_Masked():
    '''
    ::

        SASroot
          SASentry
            SASdata
              I: float[100, 512]
              Q: float[100, 512]
              Mask: int[100, 512]

    '''
    nxdata = basic_setup(get_method_name() + ".h5")
    nxdata.attrs["signal"] = "I"
    nxdata.attrs["axes"] = "Q Q".strip()
    nxdata.attrs["Q_indices"] = [0, 1]

    h = 100
    v = 512
    ds = nxdata.create_dataset("I", data=fake_data(h, v))
    ds.attrs["units"] = "1/cm"
    ds = nxdata.create_dataset("Q", data=fake_data(h, v))
    ds.attrs["units"] = "1/A"
    mask_data = numpy.int32(numpy.random.rand(h, v) + 0.5)
    ds = nxdata.create_dataset("Mask", data=mask_data)

    nxdata.file.close()


def example_07_2D_as_1D():
    '''
    ::

        SASroot
          SASentry
            SASdata
              I: float[100*512]
              Q: float[100*512]

    '''
    nxdata = basic_setup(get_method_name() + ".h5")
    nxdata.attrs["signal"] = "I"
    nxdata.attrs["axes"] = "Q"
    nxdata.attrs["Q_indices"] = 0

    h = 100
    v = 512
    ds = nxdata.create_dataset("I", data=fake_data(h * v))
    ds.attrs["units"] = "1/cm"
    ds = nxdata.create_dataset("Q", data=fake_data(h * v))
    ds.attrs["units"] = "1/A"

    nxdata.file.close()


def example_08_SANS_SAXS():
    '''
    ::

        SASroot
          SASentry
            SASdata
              @name="sans"
              @probe_type="neutron"
              I: float[100]
              Q: float[100]
            SASdata
              @name="saxs"
              @probe_type="xray"
              I: float[256]
              Q: float[256]

    '''
    nxdata = basic_setup(get_method_name() + ".h5")
    nxdata.attrs["probe_type"] = "neutron"
    nxdata.attrs["signal"] = "I"
    nxdata.attrs["axes"] = "Q"
    nxdata.attrs["Q_indices"] = 0

    n = 100
    ds = nxdata.create_dataset("I", data=fake_data(n))
    ds.attrs["units"] = "1/cm"
    ds = nxdata.create_dataset("Q", data=fake_data(n))
    ds.attrs["units"] = "1/A"

    nxentry = nxdata.parent
    nxentry.attrs["default"] = "sans"
    nxentry["sans"] = nxdata            # change the nxdata group name
    del nxentry["sasdata"]

    nxdata = nxentry.create_group("saxs")
    nxdata.attrs["NX_class"] = "NXdata"
    nxdata.attrs["SAS_class"] = "SASdata"
    nxdata.attrs["probe_type"] = "xray"

    n = 256
    ds = nxdata.create_dataset("I", data=fake_data(n))
    ds.attrs["units"] = "1/cm"
    ds = nxdata.create_dataset("Q", data=fake_data(n))
    ds.attrs["units"] = "1/A"

    nxdata.file.close()


def example_09_1D_time():
    '''
    ::

  SASroot
    SASentry
      SASdata
        @axes=Time,Q
        @Time_indices=0
        @Q_indices=1
        Time: float[nTime]  
        Q: float[100]
        I: float[nTime,100]

    '''
    nxdata = basic_setup(get_method_name() + ".h5")
    nxdata.attrs["signal"] = "I"
    nxdata.attrs["axes"] = "Time Q".split()
    nxdata.attrs["Time_indices"] = 0
    nxdata.attrs["Q_indices"] = 1

    n = 100
    nTime = 5
    ds = nxdata.create_dataset("I", data=fake_data(nTime, n))
    ds.attrs["units"] = "1/cm"
    ds = nxdata.create_dataset("Q", data=fake_data(n))
    ds.attrs["units"] = "1/A"
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
