# NXcanSAS_examples
example data files written to the NXcanSAS standard

In this repository, the example files in these directories are known
to have been written to the [NXcanSAS standard](http://download.nexusformat.org/doc/html/classes/applications/NXcanSAS.html ):

* 1d_standard/
* canSAS2012_examples/

Examples in the `others` directory are not guaranteed to conform
to the NXcanSAS standard.

## NXcanSAS: a NeXus application definition
The NXcanSAS application definition was ratified by the NIAC at their 2016 meeting
and is now part of the NeXus standard.


## File validation
It is recommended that any NXcanSAS example data file deposited here
be checked using a validation tool called 
**punx** (Python Utilities for NeXus).
It would be useful to post the validation output from punx along with the example data file.

Information about punx (currently in development) is available online: http://punx.readthedocs.io

It is planned to add a validation step to this repository so that all data files will
be checked each time the GitHub repository is updated.  This will use the travis-ci.org
continuous integration process and the punx tool described above.
