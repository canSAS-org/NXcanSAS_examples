# NXcanSAS_examples
example data files written to the NXcanSAS standard

In this repository, the example files in these directories are known
to have been written to the NXcanSAS standard (draft as of 2016-11-27):

* 1d_standard/
* canSAS2012_examples/

 Examples in other directories are not guaranteed to conform.

## NXcanSAS: a NeXus contributed definition
In NeXus, *contributed definitions* are in an *incubation*
status, during which review and revision occur by both the
proposal team and members of the NIAC.  The process to **ratify** the
NXcanSAS will move it to become one of the NeXus *application definitions*
so that it becomes a permanent part of the NeXus standard.

The NXcanSAS application definition was ratified by the NIAC at their 2016 meeting.
The canSAS Data Formats Working Group is finalizing the details in the specification.
See the issue here: "move NXcanSAS to applications" at
https://github.com/nexusformat/definitions/issues/492


## Recommendation
It is recommended that any NXcanSAS example data file deposited here
be checked using a validation tool called 
**punx** (Python Utilities for NeXus).
It would be useful to post the validation output from punx along with the example data file.

Information about punx (currently in development) is available online: http://punx.readthedocs.io

It is planned to add a validation step to this repository so that all data files will
be checked each time the GitHub repository is updated.  This will use the travis-ci.org
continuous integration process and the punx tool described above.
