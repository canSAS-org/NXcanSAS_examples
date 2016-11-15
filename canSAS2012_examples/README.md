# Models

## note: 2016-11-15,prj

  These notes are not consistent with the examples created.
  For **all** examples, consult the documentation in the
  python code that created the example.

## Common cases

### 1-D I(Q)


  This model could describe data stored in the the canSAS1d/1.0 format (with the addition of 
  *uncertainty* data and some additional metadata).



  SASroot
    SASentry
      SASdata
        @Q_indices=0
        @I_axes=Q
        I: float[100]
        Q: float[100]



### 2-D image

  
  SASroot
    SASentry
      SASdata
        @Q_indices=0,1
        @I_axes=Q,Q
        I: float[100, 512]
        Qx: float[100, 512]
        Qy: float[100, 512]
        Qz: float[100, 512]


### 2-D (image)  I(|Q|) +/- sigma(|Q|)

  SASroot
    SASentry
      SASdata
        @Q_indices=0,1
        @I_axes=Q,Q
        I: float[300, 300]
          @uncertainty=Idev
        Q: float[300, 300]
        Idev: float[300, 300]

### 2-D SAS/WAS images

Consider the multi-technique experiment that produces 
small-angle and wide-angle scattering data images.  
The reduced data results in images as well.  
Each image might be described separately (see the model for SAS using 
several detectors  for an alternative).  
Here the SAS data image is 100 x 512 pixels.  
The WAS data (not covered by this canSAS standard) is 256 x 256 pixels.
    
  SASroot
    SASentry
      SASdata
        @name="sasdata"
        @Q_indices=0,1
        @I_axes=Q,Q
        I: float[100, 512]
        Qx: float[100, 512]
        Qy: float[100, 512]
        Qz: float[100, 512]
      SASdata
        @name="wasdata"
        @Q_indices=0,1
        @I_axes=Q,Q
        I: float[256, 256]
        Qx: float[256, 256]
        Qy: float[256, 256]
        Qz: float[256, 256]

### 2-D masked image
  
  SASroot
    SASentry
      SASdata
        @Q_indices=0,1
        @I_axes=Q,Q
        @Mask_indices=0,1
        I: float[100, 512]
        Qx: float[100, 512]
        Qy: float[100, 512]
        Qz: float[100, 512]
        Mask: int[100, 512]




### 2-D generic I(Q)

Could use this model, for example, to describe data from multiple detectors (by listing individual 
pixels from all detectors retained after any masking).  Or, could describe data from one detector 
of any geometry.  This is the most flexible.

Examples:     
:download:`HDF5 <../../examples/hdf5/generic2dcase.h5>`
:download:`XML <../../examples/xml/generic2dcase.xml>`

  
  SASroot
    SASentry
      SASdata
        @Q_indices=0
        @I_axes=Q
        I: float[100*512]
        Qx: float[100*512]
        Qy: float[100*512]
        Qz: float[100*512]

### 2-D SANS and SAXS

Consider the multi-technique experiment that produces 
small-angle neutron and X-ray scattering data. 
Here the SANS data image is 100 x 512 pixels and
the SAXS data is 256 x 256 pixels.  (Normally, you will
need more metadata for each probe, such as wavelength, to
make a full analysis using both datasets.)

  
  SASroot
    SASentry
      SASdata
        @name="sans"
        @probe_type="neutron"
        @Q_indices=0
        @I_axes=Q
        I: float[100*512]
        Qx: float[100*512]
        Qy: float[100*512]
        Qz: float[100*512]
      SASdata
        @name="saxs"
        @probe_type="xray"
        @Q_indices=0
        @I_axes=Q
        I: float[256*256]
        Qx: float[256*256]
        Qy: float[256*256]
        Qz: float[256*256]



### several detectors

Here, the data are appended to a common ``I`` data object.
This hypothetical case has reduced data derived from 
three detectors, I_a(Q), I_b(Q), and I_c(Q).
Also, a certain number of pixels (``nDiscardedPixels``) have been discarded
previously from the data for various reasons.
  
  .. tip::  Typical data might have fewer useful pixels due to various
    detector artifacts such as zingers, streaks, and dead spots, as well
    as an applied intensity mask.  There is no need to write such useless pixels
    to the data objects.

  ==============  ========   ====================
  intensity       detector   shape
  ==============  ========   ====================
  :math:`I_a(Q)`  2-D        100 x 512 pixels
  :math:`I_b(Q)`  1-D        2000 pixels
  :math:`I_c(Q)`  2-D        256 x 256 pixels
  ==============  ========   ====================

  Data from a SAXS/MAXS/WAXS instrument might be represented thus.

    
  SASroot
    SASentry
      SASdata
        @Q_indices=0
        @I_axes=Q
        I: float[100*512  + 2000 + 256*256 - nDiscardedPixels]
        Qx: float[100*512 + 2000 + 256*256 - nDiscardedPixels]
        Qy: float[100*512 + 2000 + 256*256 - nDiscardedPixels]
        Qz: float[100*512 + 2000 + 256*256 - nDiscardedPixels]



## I(t,Q) models with time-dependence

### 1-D I(t,Q)
  
  SASroot
    SASentry
      SASdata
        @I_axes=Time,Q
        @Time_indices=0
        @Q_indices=1
        Time: float[nTime]  
        Q: float[100]
        I: float[nTime,100]

### 1-D I(t,Q(t))

This example is slightly more complex, showing data where :math:`Q` is also time-dependent.

    
  SASroot
    SASentry
      SASdata
        @Q_indices=0,1
        @Time_indices=0
        @I_axes=Time,Q
        I: float[nTime,100]
        Q: float[nTime,100]
        Time: float[nTime]

.. _1D SAS data in a time series I(t,Q(t)) +/- Idev(t,Q(t)):

### 1-D I(t,Q(t))\pm\sigma(t,Q(t))

Now, provide the uncertainties (where ``Idev`` represents 
\sigma(t,Q(t)) ) of the intensities:

    
  SASroot
    SASentry
      SASdata
        @Q_indices=0,1
        @Time_indices=0
        @I_axes=Time,Q
        I: float[nTime,100]
          @uncertainty=Idev
        Idev: float[nTime,100]
        Q: float[nTime,100]
        Time: float[nTime]


### 2-D I(t,Q)
  
  SASroot
    SASentry
      SASdata
        @Q_indices=1
        @Time_indices=0
        @I_axes=Time,Q
        I: float[nTime,100*512]
        Qx: float[100*512]
        Qy: float[100*512]
        Qz: float[100*512]
        Time: float[nTime]

.. _2-D I(t,Q(t)):

### 2-D I(t,Q(t))

This example is slightly more complex, showing data where :math:`Q` is also time-dependent.

  
  SASroot
    SASentry
      SASdata
        @Q_indices=0,1
        @Time_indices=0
        @I_axes=Time,Q
        I: float[nTime,100*512]
        Qx: float[nTime,100*512]
        Qy: float[nTime,100*512]
        Qz: float[nTime,100*512]
        Time: float[nTime]

.. _2-D.time-dependent.masked.image:

### 2-D I(t,Q(t)) masked image

This example explores a bit more complexity, adding a mask that is time-dependent.

  
  SASroot
    SASentry
      SASdata
        @Q_indices=0,1,2
        @I_axes=Time,Q,Q
        @Mask_indices=1,2
        @MTime_indices=0
        I: float[nTime,100,512]
        Qx: float[nTime,100,512]
        Qy: float[nTime,100,512]
        Qz: float[nTime,100,512]
        Time: float[nTime]
        Mask: int[100,512]



## models with several varied parameters

### 2-D I(t,T,P,Q(t,T,P))

Complex case of I(t,T,P,Q(t,T,P))
where all :math:`Q` values are different for each combination of time, temperature, and pressure.

    
  SASroot
    SASentry
      SASdata
        @Time_indices=0
        @Temperature_indices=1
        @Pressure_indices=2
        @Q_indices=0,1,2,3
        @I_axes=Time,Temperature,Pressure,Q
        I: float[nTime,nTemperature,nPressure,100*512]
        Qx: float[nTime,nTemperature,nPressure,100*512]
        Qy: float[nTime,nTemperature,nPressure,100*512]
        Qz: float[nTime,nTemperature,nPressure,100*512]
        Time: float[nTime]
        Temperature: float[nTemperature]
        Pressure: float[nPressure]


### 2-D  I(T,t,P,Q(t)) images

Slightly less complex than previous, now :math:`I(T,t,P,Q(t))`
where :math:`Q` only depends on time.

  
  SASroot
    SASentry
      SASdata
        @Temperature_indices=0
        @Time_indices=1
        @Pressure_indices=2
        @Q_indices=1,3,4
        @I_axes=Temperature,Time,Pressure,Q,Q
        I: float[nTemperature,nTime,nPressure,100,512]
        Qx: float[nTime,100,512]
        Qy: float[nTime,100,512]
        Qz: float[nTime,100,512]
        Time: float[nTime]
        Temperature: float[nTemperature]
        Pressure: float[nPressure]


## Complicated Uncertainties

The uncertainties might be derived from several factors, or there may even be
several uncertainties contributing.  In practical terms, these are special 
cases for analysis software.  In the interest of completeness, it is 
interesting to describe how they might be represented.


### Representing Uncertainty Components

It is possible to represent the components that contribute
to the uncertainty by use of a subgroup.  Add a *@components* attribute
to the principal uncertainty, naming the subgroup that contains the 
contributing datasets.

As with all uncertainties, each component should have the same *shape* 
(rank and dimensions) as its parent dataset.

Note that a *@basis* attribute indicates how this uncertainty was determined.
The values are expected to be a short list, as yet unspecified.


  SASroot
    SASentry
      SASdata
        @Q_indices=0
        @I_axes=Q
        Q : float[nI]
        I : float[nI]
           @uncertainty=Idev
        Idev : float[nI]
           @components=I_uncertainties
        I_uncertainties:
           electronic : float[nI]
              @basis="Johnson noise"
           counting_statistics: float[nI]
              @basis="shot noise"
           secondary_standard: float[nI]
              @basis="esd"



### Representing Multiple Uncertainties (*proposed*)

.. note::  This is just a proposition.  It is based on the assumption
   that some analysis method might actually know how to handle this case.

If more than one uncertainty contributes to the intensity (and the method
described above in :ref:`representing uncertainty components` 
is not appropriate), it is proposed to
name more than one uncertainty dataset in the *@uncertainty* attribute.
The first member in this list would be the principal uncertainty.
The *@basis* attribute can be used to further describe each uncertainty.
One example be: 


  SASroot
    SASentry
      SASdata
        @Q_indices=0
        @I_axes=Q
        Q : float[nI]
        I : float[nI]
          @uncertainty=Idev,Ierr
        Idev : float[nI]
          @basis="esd"
        Ierr : float[nI]
          @basis="absolute intensity calibration"




## Unhandled Cases

### 2-D image with Q_x & Q_y vectors

This model is outside the scope of this format.  The method of addressing 
the :math:`Q` values is different than for the other models.

.. Is this really true?
.. This usage seems quite common and should be able to be handled.

    
  SASroot
    SASentry
      SASdata
        @Q_indices=*,*
        @I_axes=???
        I: float[100, 512]
        Qx: float[100]
        Qy: float[512]

Instead, use either the model titled: 
`2-D image <simple 2-D (image) I(Q)>`_
or `2-D generic data <generic 2-D I(Q)>`_ (preferred).
