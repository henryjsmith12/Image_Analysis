#!/usr/bin/env python
# -*- coding: utf-8 -*-

# -----------------------------------------------------------------------------
# :author:    Pete R. Jemian
# :email:     prjemian@gmail.com
# :copyright: (c) 2014-2020, Pete R. Jemian
#
# Distributed under the terms of the Creative Commons Attribution 4.0 International Public License.
#
# The full license is in the file LICENSE.txt, distributed with this software.
# -----------------------------------------------------------------------------


"""
Provides a set of classes to read the contents of a SPEC data file.

:author: Pete Jemian
:email: jemian@anl.gov

:meth:`~spec2nexus.spec.SpecDataFile` is the only class users will need to call.
All other :mod:`~spec2nexus.spec` classes are called from this class.
The :meth:`~spec2nexus.spec.SpecDataFile.read` method is called automatically.

The user should create a class instance for each spec data file,
specifying the file reference (by path reference as needed)
and the internal routines will take care of all that is necessary
to read and interpret the information.

.. autosummary::

    ~is_spec_file
    ~is_spec_file_with_header
    ~SpecDataFile
    ~SpecDataFileHeader
    ~SpecDataFileScan


..  -----------------------------------------------------------------------------------------
    old documentation
    -----------------------------------------------------------------------------------------

    .. index:: SPEC data file structure

    The parser makes the assumption that a SPEC data file is composed from
    a sequence of component blocks.  The component blocks are either header
    or scan blocks.  Header blocks have the first line starting with ``#F``
    while scan blocks have the first line starting with ``#S``.  Usually,
    there is only one header block in a SPEC data file, followed by many
    scan blocks.  The header block contains information common to all the
    scan blocks that follow it.  Content for each block continues until
    the next block starts or the file ends.  The pattern is:

    * #F line starts a header block
    * there could be multiple #F lines in a data file
    * #S lines start a SPEC scan
    * everything between #F and the next #S is header content
    * everything after a #S line is scan content (until EOF, the next #S or the next #F)

    .. rubric:: Additional assumptions

    * Lines that begin with ``#`` contain metadata of some form.
    * Lines that begin with ``@`` contain MCA data
    * Lines that begin with a number are data points
    * Line that are blank will be ignored
    * Lines that begin with anything else are unexpected and will be ignored

    For lines that begin with ``#``, these hold keys to some form of metadata.
    Some of the keys are identified and used by the SPEC standard.mac (and other)
    macro files.  Other keys are left to the user to define.  There are two
    general types of key, best described by a regular expression:

    ====================  ============  ============================
    regexp                example       how it appears
    ====================  ============  ============================
    ``^#[a-zA-Z]+\s``     ``#S``        by itself
    ``^#[a-zA-Z]+\d+\s``  ``#P5``       part of a numbered series
    ====================  ============  ============================

    Note that keys that appear as part of a numbered series (such as ``#O0 #O1 #O2`` ...),
    usually have numbers starting at 0.
    -----------------------------------------------------------------------------------------

Note that the SPEC geometry control lines (``#G0 #G1`` ...)
have meanings that are unique to specific diffractometer geometries including
different numbers of values.  Consult the geometry macro file for specifics.



.. rubric:: Examples

Get the first and last scan numbers from the file:

    >>> from spec2nexus import spec
    >>> spec_data = spec.SpecDataFile('path/to/my/spec_data.dat')
    >>> print(spec_data.fileName)
    path/to/my/spec_data.dat
    >>> print('first scan: ', spec_data.getFirstScanNumber())
    1
    >>> print('last scan: ', spec_data.getLastScanNumber())
    22

Get plottable data from scan number 10:

    >>> from spec2nexus import spec
    >>> spec_data = spec.SpecDataFile('path/to/my/spec_data.dat')
    >>> scan10 = spec_data.getScan(10)
    >>> x_label = scan10.L[0]
    >>> y_label = scan10.L[-1]
    >>> x_data = scan10.data[x_label]
    >>> y_data = scan10.data[y_label]


Try to read a file that does not exist:

    >>> spec_data = spec.SpecDataFile('missing_file')
    Traceback (most recent call last):
      ...
    spec.SpecDataFileNotFound: file does not exist: missing_file

.. rubric::  Classes and Methods

"""

from collections import OrderedDict
import os
import time
from . import plugin


UNRECOGNIZED_KEY = "unrecognized_control_line"
MCA_DATA_KEY = "_mca_"


class SpecDataFileNotFound(IOError):
    """data file was not found"""


class SpecDataFileCouldNotOpen(IOError):
    """data file could not be opened"""


class NotASpecDataFile(Exception):
    """content of file is not SPEC data (first line must start with ``#F``)"""


class DuplicateSpecScanNumber(Exception):
    """multiple use of scan number in a single SPEC data file"""


class UnknownSpecFilePart(Exception):
    """unknown part in a single SPEC data file"""


def is_spec_file(filename):
    """
    test if a given file name is a SPEC data file

    :param str filename: path/to/possible/spec/data.file

    *filename* is a SPEC file if it contains at least one #S control line
    """
    if not os.path.exists(filename) or not os.path.isfile(filename):
        return False
    try:
        with open(filename, "r") as fp:
            for line in fp.readlines():
                if line.startswith("#S "):
                    return True
    except Exception:
        pass
    return False


def is_spec_file_with_header(filename):
    """
    test if a given file name is a SPEC data file

    :param str filename: path/to/possible/spec/data.file

    *filename* is a SPEC file only if the file starts [#]_
    with these control lines in order:

    * #F    - original filename
    * #E    - the UNIX epoch (seconds from 00:00 GMT 1/1/70)
    * #D    - current date and time in UNIX format
    * #C    - comment line (the first one provides the filename again and the user name)

    such as::

        #F LNO_LAO
        #E 1276730676
        #D Wed Jun 16 18:24:36 2010
        #C LNO_LAO  User = epix33bm

    .. [#] SPEC manual, *Standard Data File Format*, http://www.certif.com/spec_manual/user_1_4_1.html
    """
    if not os.path.exists(filename) or not os.path.isfile(filename):
        return False
    expected_controls = ("#F ", "#E ", "#D ", "#C ")
    try:
        lines = open(filename).readlines()[: len(expected_controls)]
    except UnicodeDecodeError:
        return False
    if len(lines) != len(expected_controls):
        return False
    for expected, line in zip(expected_controls, lines):
        if not line.startswith(expected):
            return False
    return True


# -------------------------------------------------------------------------------------------


class SpecDataFile(object):

    """
    contents of a SPEC data file

    .. autosummary::

        ~dissect_file
        ~getFirstScanNumber
        ~getLastScanNumber
        ~getMaxScanNumber
        ~getMinScanNumber
        ~getScan
        ~getScanCommands
        ~getScanNumbers
        ~getScanNumbersChronological
        ~read
        ~refresh
        ~update_available

    """

    fileName = ""
    parts = ""
    headers = []
    scans = {}
    readOK = -1

    def __init__(self, filename):
        self.fileName = None
        self.headers = []
        self.scans = OrderedDict()
        self.readOK = -1
        self.last_scan = None
        self.mtime = 0
        self.filesize = 0

        if filename is not None:
            if not os.path.exists(filename):
                raise SpecDataFileNotFound(
                    "file does not exist: " + str(filename)
                )
            if not is_spec_file(filename):
                raise NotASpecDataFile(
                    "not a SPEC data file: " + str(filename)
                )
            self.fileName = filename

            self.read()

    def __str__(self):
        return self.fileName or "None"

    @property
    def update_available(self):
        """
        Has the file been updated since the last time it was read?

        Reference file modification time is stored *after*
        file is read in :meth:`read()` method.

        EXAMPLE USAGE

        Open the SPEC data file (example):

            sdf = spec.SpecDataFile(filename)

        then, monitor (continuing example):

            if sdf.update_available:
                myLastScan = sdf.last_scan
                sdf.read()
                plot_scan_and_newer(myLastScan)    # new method
                myLastScan = sdf.last_scan

        .. note: The previous last_scan is reprocessed since
           that scan may not have been complete when the file
           was read() previously.

        """
        same_mtime = self.mtime == os.path.getmtime(self.fileName)
        same_size = self.filesize == os.path.getsize(self.fileName)
        identical = same_mtime and same_size
        return not identical

    def refresh(self):
        """
        update (refresh) the content if the file is updated

        returns previous last_scan or None if file not updated

        .. caution:  previous last_scan must be re-created if updated

           After calling :meth:`refresh()`, any client
           with an object of the previous last scan
           should get a new object with the update data.

           EXAMPLE::

               scan = sdf.getScan(42)
               checkpoint = sdf.refresh()
               if checkpoint is not None:
                   scan = sdf.getScan(checkpoint)    # get updates

        """
        if self.update_available:
            previous_scan = self.last_scan

            self.read()
            return previous_scan
        return None

    def _read_file_(self, spec_file_name):
        """Reads a spec data file"""
        if not os.path.exists(spec_file_name):
            raise SpecDataFileNotFound(
                "file does not exist: " + str(spec_file_name)
            )
        try:
            with open(spec_file_name, "r") as fp:
                buf = fp.read()
        except IOError:
            msg = "Could not open spec file: " + str(spec_file_name)
            raise SpecDataFileCouldNotOpen(msg)
        if not is_spec_file(spec_file_name):
            msg = "Not a spec data file: " + str(spec_file_name)
            raise NotASpecDataFile(msg)

        # caution: some files may have EOL = \r\n
        # convert all '\r\n' to '\n', then all '\r' to '\n'

        return buf.replace("\r\n", "\n").replace("\r", "\n")

    def dissect_file(self):
        """
        divide (SPEC data file text) buffer into sections

        internal: A *block* starts with either #F | #E | #S

        RETURNS

        [block]
            list of blocks where each block is one or more lines of
            text with one of the above control lines at its start

        """
        buf = self._read_file_(self.fileName).splitlines()

        sections, block = [], []

        for _line_num, text in enumerate(buf):
            if len(text.strip()) > 0:
                f = text.split()[0]
                if len(f) == 2 and f in ("#E", "#F", "#S"):
                    if len(block) > 0:
                        sections.append("\n".join(block))
                    block = []
            block.append(text)

        if len(block) > 0:
            sections.append("\n".join(block))
        return sections

    def read(self):
        """Reads and parses a spec data file"""
        manager = plugin.get_plugin_manager()
        sections = self.dissect_file()
        for block in sections:
            if len(block) == 0:
                continue
            key = manager.getKey(block.splitlines()[0])
            manager.process(key, block, self)

            if key == "#S":
                scan = list(self.scans.values())[-1]
                for line in scan.raw.splitlines()[1:]:
                    if len(line) > 0:
                        key = line.split()[0]
                        if key in ("#D",):
                            manager.process(key, line, scan)
                            break

        # fix any missing parts
        if not hasattr(self, "specFile"):
            self.specFile = self.fileName

        self.last_scan = self.getLastScanNumber()
        self.filesize = os.path.getsize(self.fileName)
        self.mtime = os.path.getmtime(self.fileName)

    def getScan(self, scan_number=0):
        """return the scan number indicated, None if not found"""
        if int(float(scan_number)) < 1:
            # relative scan reference
            scanlist = self.getScanNumbers()
            scan_number = list(scanlist)[int(scan_number)]
        scan_number = str(scan_number)
        if scan_number in self.scans:
            return self.scans[scan_number]
        return None

    def getScanNumbers(self):
        """return a list of all scan numbers sorted by scan number"""
        keys = self.scans.keys()
        try:
            r = sorted(keys, key=int)
        except ValueError as _exc:
            r = sorted(keys, key=float)
        return r

    def getScanNumbersChronological(self):
        """return a list of all scan numbers sorted by date"""

        def byDate_key(scan):
            return time.strptime(scan.date)

        scans = sorted(self.scans.values(), key=byDate_key)
        return [_.scanNum for _ in scans]

    def getMinScanNumber(self):
        """return the lowest numbered scan"""
        return self.getScanNumbers()[0]

    def getMaxScanNumber(self):
        """return the highest numbered scan"""
        return self.getScanNumbers()[-1]

    def getFirstScanNumber(self):
        """return the first scan"""
        return self.getScanNumbersChronological()[0]

    def getLastScanNumber(self):
        """return the last scan"""
        return self.getScanNumbersChronological()[-1]

    def getScanCommands(self, scan_list=None):
        """return all the scan commands as a list, with scan number"""
        scan_list = scan_list or self.getScanNumbers()
        commands = []
        for key in scan_list:
            scan = self.getScan(key)
            if isinstance(scan, SpecDataFileScan):
                commands.append("#S " + str(key) + " " + scan.scanCmd)
        return commands


# -------------------------------------------------------------------------------------------


class SpecDataFileHeader(object):
    """
    contents of a spec data file header (#E) section

    .. autosummary::

        ~interpret
        ~addPostProcessor
        ~addH5writer
        ~getLatestScan

    """

    def __init__(self, buf, parent=None):
        # ----------- initialize the instance variables
        self.parent = parent  # instance of SpecDataFile
        self.comments = []
        self.date = ""
        self.epoch = 0
        if parent is None:
            self.file = None
        else:
            self.file = parent.fileName
        self.H = []
        self.O = []
        self.raw = buf
        self.postprocessors = {}
        self.h5writers = {}

    def interpret(self):
        """ interpret the supplied buffer with the spec data file header"""
        manager = plugin.get_plugin_manager()
        for _i, line in enumerate(self.raw.splitlines(), start=1):
            if len(line) == 0:
                continue  # ignore blank lines
            key = manager.getKey(line)
            if key is None:
                # log message instead of raise exception
                # https://github.com/prjemian/spec2nexus/issues/57
                # raise UnknownSpecFilePart("line %d: unknown header line: %s" % (_i, line))
                key = UNRECOGNIZED_KEY
                manager.process(key, line, self)
            elif key == "#E":
                pass  # avoid recursion
            else:
                # most of the work is done here
                manager.process(key, line, self)

        # call any post-processing hook functions from the plugins
        for func in self.postprocessors.values():
            func(self)

    def addPostProcessor(self, label, func):
        """
        add a function to be processed after interpreting all lines from a header

        :param str label: unique label by which this postprocessor will be known
        :param obj func: function reference of postprocessor

        The postprocessors will be called at the end of header interpretation.
        """
        if label not in self.postprocessors:
            self.postprocessors[label] = func

    def addH5writer(self, label, func):
        """
        add a function to be processed when writing the scan header

        :param str label: unique label by which this writer will be known
        :param obj func: function reference of writer

        The writers will be called when the HDF5 file is to be written.
        """
        if label not in self.h5writers:
            self.h5writers[label] = func

    def getLatestScan(self):
        return list(self.parent.scans.values())[-1]


# -------------------------------------------------------------------------------------------


class SpecDataFileScan(object):
    """
    contents of a spec data file scan (#S) section

    .. autosummary::

        ~get_macro_name
        ~interpret
        ~add_interpreter_comment
        ~get_interpreter_comments
        ~addPostProcessor
        ~addH5writer

    """

    def __init__(self, header, buf, parent=None):
        self.parent = parent  # instance of SpecDataFile
        self.comments = []
        self.data = {}
        self.data_lines = []
        self.date = ""
        self.G = {}
        self.header = header  # index number of relevant #F section previously interpreted
        self.L = []
        self.M = ""
        self.positioner = {}
        self.N = -1
        self.P = []
        self.Q = ""
        self.raw = buf
        self.S = ""
        self.scanNum = -1
        self.scanCmd = ""
        self._interpreter_comments_ = []
        if parent is not None:
            # avoid changing the interface for clients
            if isinstance(parent, SpecDataFile):
                self.specFile = parent.fileName
            elif isinstance(parent, SpecDataFileHeader):
                self.specFile = parent.parent.fileName
        elif self.header is not None:
            if self.header.parent is not None:
                self.specFile = self.header.parent.fileName
        else:
            self.specFile = None
        self.T = ""
        self.V = []
        self.column_first = ""
        self.column_last = ""
        self.postprocessors = {}
        self.h5writers = {}

        # the attributes defined in PluginManager().lazy_attributes
        # are set only after a call to self.interpret()
        # That call is triggered on the first call for any of these attributes.
        self.__lazy_interpret__ = True
        self.__interpreted__ = False

    def __str__(self):
        return self.S

    def __getattribute__(self, attr):
        manager = plugin.get_plugin_manager()
        if attr in manager.lazy_attributes:
            if self.__lazy_interpret__:
                self.interpret()
        return object.__getattribute__(self, attr)

    def get_macro_name(self):
        """
        name of the SPEC macro used for this scan
        """
        return self.scanCmd.split()[0]

    def interpret(self):
        """interpret the supplied buffer with the spec scan data"""
        manager = plugin.get_plugin_manager()
        if self.__interpreted__:  # do not do this twice
            return
        self.__lazy_interpret__ = False  # set now to avoid recursion
        lines = self.raw.replace("\\\n", " ").splitlines()
        for _i, line in enumerate(lines, start=1):
            if len(line) == 0:
                continue  # ignore blank lines
            key = manager.getKey(line.lstrip())
            if key is None:
                # __s__ = '<' + line + '>'
                # _msg = "scan %s, line %d: unknown key, ignored text: %s" % (str(self.scanNum), _i, line)
                # raise UnknownSpecFilePart(_msg)
                # log message instead of raise exception
                # https://github.com/prjemian/spec2nexus/issues/57
                key = UNRECOGNIZED_KEY
                manager.process(key, line, self)
            elif key != "#S":  # avoid recursion
                # most of the work is done here
                manager.process(key, line, self)

        # call any post-processing hook functions from the plugins
        for func in self.postprocessors.values():
            func(self)

        self.__interpreted__ = True

    def add_interpreter_comment(self, comment):
        """
        allow the interpreter to communicate information to the caller

        see issue #66: https://github.com/prjemian/spec2nexus/issues/66
        """
        self._interpreter_comments_.append(comment)

    def get_interpreter_comments(self):
        """
        return the list of comments

        see issue #66: https://github.com/prjemian/spec2nexus/issues/66
        """
        return self._interpreter_comments_

    def addPostProcessor(self, label, func):
        """
        add a function to be processed after interpreting all lines from a scan

        :param str label: unique label by which this postprocessor will be known
        :param obj func: function reference of postprocessor

        The postprocessors will be called at the end of scan data interpretation.
        """
        if label not in self.postprocessors:
            self.postprocessors[label] = func

    def addH5writer(self, label, func):
        """
        add a function to be processed when writing the scan data

        :param str label: unique label by which this writer will be known
        :param obj func: function reference of writer

        The writers will be called when the HDF5 file is to be written.
        """
        if label not in self.h5writers:
            self.h5writers[label] = func

    def _interpret_data_row(self, row_text):
        buf = {}
        for col, val in enumerate(row_text.split()):
            buf[self.L[col]] = float(val)
        return buf

    def _unique_key(self, label, keylist):
        """ensure that label is not yet existing in keylist"""
        i = 0
        key = label
        while key in keylist:
            i += 1
            key = label + "_" + str(i)
            if i == 1000:
                raise RuntimeError(
                    "cannot make unique key for duplicated column label!"
                )
        return key
