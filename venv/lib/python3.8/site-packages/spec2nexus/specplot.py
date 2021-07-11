#!/usr/bin/env python

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
Plot the data from scan N in a SPEC data file

.. autosummary::

    ~Selector
    ~ImageMaker
    ~LinePlotter
    ~MeshPlotter
    ~openSpecFile

Exceptions:

.. autosummary::

    ~NoDataToPlot
    ~NotPlottable
    ~ScanAborted
    ~UnexpectedObjectTypeError

"""

import os
import numpy

from . import charts
from . import spec  # read SPEC data files
from . import singletons
from . import utils


class UnexpectedObjectTypeError(RuntimeError):

    """Incorrect Python object type: programmer error."""


class ScanAborted(RuntimeWarning):

    """Scan aborted before all points acquired."""


class NotPlottable(ValueError):

    """No plottable data for this scan."""


class NoDataToPlot(ValueError):

    """No data found."""


ABORTED_ATTRIBUTE_TEXT = "_aborted_"


class Selector(singletons.Singleton):
    """
    associate SPEC scan macro names with image makers

    :image maker: subclass of :class:`ImageMaker`

    To include a custom image maker from outside this module,
    create the subclass and then add it to an instance of this
    class.  Such as this plotter that defaults to a logarithmic
    scale for the X axis for all `logxscan` macros:

        from spec2nexus import specplot

        class LogX_Plotter(specplot.ImageMaker):

            def x_log(self):
                return True

        # ...

        selector = specplot.Selector()
        selector.add('logxscan', LogX_Plotter)

        # ...

        image_maker = specplot.Selector().auto(scan)
        plotter = image_maker()
        plotter.plot_scan(scan, fullPlotFile)

    This class is a singleton which means you will always get the same
    instance when you call this class many times in your program.

    .. autosummary::

        ~auto
        ~add
        ~update
        ~get
        ~exists
        ~default

    """

    default_key = "__default__"

    def __init__(self):
        self.db = {}
        self.add(self.default_key, LinePlotter, default=True)

    def auto(self, scan):
        """
        automatically choose a scan image maker based on the SPEC scan macro

        Selection Rules:

        * macro ends with "scan": use :class:`LinePlotter`
        * macro ends with "mesh": use :class:`MeshPlotter`
        * default: use default image maker (initially :class:`LinePlotter`)
        """
        if not isinstance(scan, (spec.SpecDataFileScan,)):
            msg = "expected a SPEC scan object, received: "
            msg += str(scan)
            raise UnexpectedObjectTypeError(msg)

        macro = scan.get_macro_name()
        if self.exists(macro):
            return self.get(macro)

        # adapt for different scan macros
        image_maker = self.default()
        if macro == "hklscan":
            image_maker = HKLScanPlotter
        elif macro.lower().endswith("scan"):
            image_maker = LinePlotter
        elif macro.lower().endswith("mesh"):
            image_maker = MeshPlotter

        # register this macro name
        self.add(macro, image_maker)
        return image_maker

    def add(self, key, value, default=False):
        """
        register a new value by key

        :param str key: name of key, typically the macro name
        :raises KeyError: if key exists
        :raises UnexpectedObjectTypeError: if value is not subclass of :class:`ImageMaker`
        """
        if self.exists(key):
            raise KeyError("key exists: " + key)
        if not issubclass(value, ImageMaker):
            msg = "expected subclass of ImageMaker, received type: "
            msg += type(value).__name__
            raise UnexpectedObjectTypeError(msg)

        self.db[key] = value
        if default:
            self.db[self.default_key] = value

        return value

    def update(self, key, value, default=False):
        """
        replace an existing key with a new value

        :param str key: name of key, typically the macro name
        :raises KeyError: if key does not exist
        :raises UnexpectedObjectTypeError: if value is not subclass of :class:`ImageMaker`
        """
        if not self.exists(key):
            raise KeyError("key does not exist: " + key)
        if not issubclass(value, ImageMaker):
            msg = "expected subclass of ImageMaker, received type: "
            msg += type(value).__name__
            raise UnexpectedObjectTypeError(msg)

        self.db[key] = value
        if default:
            self.db[self.default_key] = value

        return value

    def get(self, key):
        """
        return a value by key

        :returns: subclass of :class:`ImageMaker` or `None` if key not found
        """
        return self.db.get(key)

    def exists(self, key):
        """
        is the key known?
        """
        return key in self.db

    def default(self):
        """
        retrieve the value of the default key
        """
        return self.get(self.default_key)


class ImageMaker(object):
    """
    superclass to handle plotting of data from a SPEC scan

    .. rubric:: Internal data model

    :signal: name of the ``signal`` data (default data to be plotted)
    :data: values of various collected arrays {label: array}
    :axes: names of the axes of signal data

    .. rubric:: USAGE:

    #. Create a subclass of :class:`ImageMaker`
    #. Override any of these methods:

       .. autosummary::

            ~data_file_name
            ~make_image
            ~plottable
            ~plot_options
            ~retrieve_plot_data

    .. rubric:: EXAMPLE

    ::

        class LinePlotter(ImageMaker):
            '''create a line plot'''

            def make_image(self, plotFile):
                '''
                make MatPlotLib chart image from the SPEC scan

                :param obj plotData: object returned from :meth:`retrieve_plot_data`
                :param str plotFile: name of image file to write
                '''
                assert(self.signal in self.data)
                assert(len(self.axes) == 1)
                assert(self.axes[0] in self.data)

                y = self.data[self.signal]
                x = self.data[self.axes[0]]
                xy_plot(x, y,  plotFile,
                       title = self.plot_title(),
                       plot_subtitle = self.plot_subtitle(),
                       xtitle = self.x_title(),
                       ytitle = self.y_title(),
                       xlog = self.x_log(),
                       ylog = self.y_log(),
                       timestamp_str = self.timestamp())

        sfile = specplot.openSpecFile(specFile)
        scan = sfile.getScan(scan_number)
        plotter = LinePlotter()
        plotter.plot_scan(scan, plotFile, y_log=True)

    """

    def __init__(self):
        self.scan = None
        self.settings = self._initialize_settings_()
        self.signal = None
        self.axes = []
        self.data = {}

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # support methods that a subclass might override

    def data_file_name(self):
        """
        the name of the file with the actual data

        Usually, this is the SPEC data file
        but it *could* be something else
        """
        return self.scan.header.parent.fileName  # self.scan.specFile

    def make_image(self, plotFile):
        """
        make MatPlotLib chart image from the SPEC scan

        The data to be plotted are provided in:

        * `self.signal`
        * `self.axes`
        * `self.data`

        :param str plotFile: name of image file to write
        """
        raise NotImplementedError(
            "must implement make_image() in each subclass"
        )

    def plottable(self):
        """
        can this data be plotted as expected?
        """
        return False  # override in subclass with specific tests

    def plot_options(self):
        """
        re-define any plot options in a subclass
        """
        pass

    def retrieve_plot_data(self):
        """
        retrieve default plottable data from spec data file and store locally

        This method must retrieve the data to be plotted, either from the
        SPEC data file scan or from a file which name is provided
        in the scan detalis.

        These attributes must be set by this method:

        :data: dictionary containing values of the various collected arrays {label: array}
        :signal: name of the 'signal' data (default data to be plotted)
        :axes: names of the axes of signal data

        .. rubric:: Example data

        ::

            self.data = {
                'angle': [1, 2, 3, 4, 5],
                'counts': [0. 2. 55. 3. 0]}
            self.signal = 'counts'
            self.axes = ['angle']

        Raise any of these exceptions as appropriate:

        .. autosummary::

            ~NoDataToPlot
            ~NotPlottable
            ~ScanAborted

        """
        raise NotImplementedError(
            "must implement retrieve_plot_data() in each subclass"
        )

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # support methods that will not need to be defined in a subclass

    def data_is_newer_than_plot(self, plotFile):
        """only proceed if mtime of SPEC data file is newer than plotFile"""
        mtime_sdf = os.path.getmtime(self.data_file_name())
        if os.path.exists(plotFile):
            mtime_pf = os.path.getmtime(plotFile)
        else:
            mtime_pf = 0

        return mtime_sdf > mtime_pf

    def plot_scan(self, scan, plotFile, maker=None):
        """
        make an image plot of the data in the scan

        :param obj scan: instance of :class:`~spec2nexus.spec.SpecDataFileScan`
        :param str plotFile: file name for plot output
        """
        if not isinstance(scan, (spec.SpecDataFileScan,)):
            raise UnexpectedObjectTypeError(
                "scan object not a SpecDataFileScan"
            )
        if hasattr(scan, ABORTED_ATTRIBUTE_TEXT):
            match_text = "Scan aborted after 0 points."
            if scan.__getattribute__(ABORTED_ATTRIBUTE_TEXT) == match_text:
                raise ScanAborted(match_text)

        self.scan = scan

        self.set_plot_title(self.plot_title() or self.data_file_name())
        self.set_plot_subtitle(
            self.plot_subtitle()
            or "#" + str(self.scan.scanNum) + ": " + self.scan.scanCmd
        )
        self.set_timestamp(self.timestamp() or self.scan.date)

        try:
            self.retrieve_plot_data()
        except KeyError as _exc:
            if hasattr(self.scan, ABORTED_ATTRIBUTE_TEXT):
                raise ScanAborted(
                    self.scan.__getattribute__(ABORTED_ATTRIBUTE_TEXT)
                )
            raise _exc

        self.plot_options()

        if self.plottable() and self.data_is_newer_than_plot(plotFile):
            self.make_image(plotFile)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # support the self.settings dictionary with get & set methods

    def _initialize_settings_(self):
        """
        initial values are set to `None`

        subclasses that set a value should first check if the value has already been set
        unless explicitly replacing any customizations by the user
        """
        return dict(
            title=None,
            subtitle=None,
            x_title=None,
            y_title=None,
            x_log=None,
            y_log=None,
            z_log=None,
            timestamp=None,
        )

    # TODO: apply property and setter decorations

    def plot_title(self):
        """Return the plot title."""
        return self.settings["title"]

    def set_plot_title(self, text):
        """Set the plot title."""
        self.settings["title"] = text

    def plot_subtitle(self):
        """Return the plot_subtitle."""
        return self.settings["subtitle"]

    def set_plot_subtitle(self, text):
        """Set the plot_subtitle."""
        self.settings["subtitle"] = text

    def x_title(self):
        """Return the title for the X axis."""
        return self.settings["x_title"]

    def set_x_title(self, text):
        """Set the x axis title."""
        self.settings["x_title"] = text

    def y_title(self):
        """Return the title for the Y axis."""
        return self.settings["y_title"]

    def set_y_title(self, text):
        """Set the y axis title."""
        self.settings["y_title"] = text

    def x_log(self):
        """Boolean: should the X axis be plotted on a log scale?"""
        return self.settings["x_log"]

    def set_x_log(self, choice):
        """Set the x axis logarithmic if True."""
        self.settings["x_log"] = choice

    def y_log(self):
        """Boolean: should the Y axis be plotted on a log scale?"""
        return self.settings["y_log"]

    def set_y_log(self, choice):
        """Set the y axis logarithmic if True."""
        self.settings["y_log"] = choice

    def z_log(self):
        """Boolean: should the Z axis (image) be plotted on a log scale?"""
        return self.settings["z_log"]

    def set_z_log(self, choice):
        """Set the z axis (image) logarithmic if True."""
        self.settings["z_log"] = choice

    def timestamp(self):
        """Return the time of this scan as a string."""
        return self.settings["timestamp"]

    def set_timestamp(self, text):
        """Set the plot time stamp."""
        self.settings["timestamp"] = text


class LinePlotter(ImageMaker):
    """
    create a line plot
    """

    def make_image(self, plotFile):
        """
        make MatPlotLib chart image from the SPEC scan

        :param str plotFile: name of image file to write
        """
        assert self.signal in self.data
        assert len(self.axes) == 1
        assert self.axes[0] in self.data

        y = self.data[self.signal]
        x = self.data[self.axes[0]]
        ts = self.timestamp()

        charts.xy_plot(
            x,
            y,
            plotFile,
            title=self.plot_title(),
            subtitle=self.plot_subtitle(),
            xtitle=self.x_title(),
            ytitle=self.y_title(),
            xlog=self.x_log(),
            ylog=self.y_log(),
            timestamp_str=ts,
        )

    def plottable(self):
        """
        can this data be plotted as expected?
        """
        if self.signal in self.data:
            signal = self.data[self.signal]
            if (
                signal is not None
                and len(signal) > 0
                and len(self.axes) == 1
            ):
                if len(signal) == len(self.data[self.axes[0]]):
                    return True
        return False

    def plot_options(self):
        """
        define the settings for this, accepting any non-default values first
        """
        self.x_title() or self.set_x_title(self.axes[0])
        self.y_title() or self.set_y_title(self.signal)
        self.x_log() or self.set_x_log(False)
        self.y_log() or self.set_y_log(False)
        self.set_z_log(False)

    def retrieve_plot_data(self):
        """retrieve default data from spec data file"""
        # plot last column v. first column
        assert isinstance(self.scan, spec.SpecDataFileScan)
        self.signal = self.scan.column_last
        if self.signal not in self.scan.data:
            raise NoDataToPlot(str(self.scan))
        self.axes = [
            self.scan.column_first,
        ]
        self.data = {
            label: self.scan.data.get(label)
            for label in self.scan.L
            if label in self.scan.data
        }


class HKLScanPlotter(LinePlotter):
    """
    create a line plot from hklscan macros
    """

    def retrieve_plot_data(self):
        """retrieve default data from spec data file"""
        # standard hklscan macro handling
        # find the real scan axis, the one that changes
        for axis in "H K L".split():
            data = self.scan.data.get(axis)
            if data is None:
                continue
            # could compare start & end from scanCmd, this looks simpler
            if min(data) != max(data):
                # tell it to use this axis instead
                self.axes = [
                    axis,
                ]
                break

        # if not found, default changes nothing
        if data is None:
            raise NotPlottable("no data in scan: " + str(self.scan))

        if len(self.axes) == 0:
            # issue #99:  file: lmn40.spe, scan 244, hkl all fixed
            axis = "data point number"
            data = range(1, 1 + len(self.scan.data["H"]))
            self.scan.data[axis] = data
            self.set_x_title(axis + " (hkl all held constant)")
            self.axes = [
                axis,
            ]

        self.scan.column_first = axis
        self.data[axis] = data
        self.signal = self.scan.column_last
        self.data[self.signal] = self.scan.data[self.signal]


class MeshPlotter(ImageMaker):
    """
    create a mesh plot (2-D image)

    ..rubric:: References:

    :mesh 2-D parser: http://www.certif.com/spec_help/mesh.html

        ::

            mesh motor1 start1 end1 intervals1 motor2 start2 end2 intervals2 time

    :hklmesh 2-D parser: http://www.certif.com/spec_help/hklmesh.html

        ::

            hklmesh Q1 start1 end1 intervals1 Q2 start2 end2 intervals2 time

    """

    # see code in: writer.Writer.mesh()        self._mesh_(scan)

    def make_image(self, plotFile):
        """
        make MatPlotLib chart image from the SPEC scan

        :param str plotFile: name of image file to write
        """
        if len(self.axes) == 2:
            image = self.data[self.signal]
            self.set_plot_subtitle(
                "%s,  %s" % (self.signal, self.scan.raw.splitlines()[0])
            )
            self.set_x_title(self.axes[0])
            self.set_y_title(self.axes[1])

            charts.make_png(
                image,
                plotFile,
                [self.data[axis] for axis in self.axes],
                title=self.plot_title(),
                subtitle=self.plot_subtitle(),
                timestamp_str=self.timestamp(),
                xtitle=self.x_title(),
                ytitle=self.y_title(),
                log_image=self.z_log(),
            )
        elif len(self.axes) == 1:
            # fallback to 1-D plot
            y = self.data[self.signal]
            x = self.data[self.axes[0]]
            charts.xy_plot(
                x,
                y,
                plotFile,
                title=self.plot_title(),
                subtitle=self.plot_subtitle(),
                xtitle=self.x_title(),
                ytitle=self.y_title(),
                xlog=self.x_log(),
                ylog=self.y_log(),
                timestamp_str=self.timestamp(),
            )

    def plottable(self):
        """
        can this data be plotted as expected?
        """
        try:
            assert self.signal in self.data
            signal = numpy.array(self.data[self.signal])
            assert len(self.axes) in (0, len(signal.shape))
            for order, axis in enumerate(reversed(self.axes)):
                assert axis in self.data
                assert signal.shape[order] == len(self.data[axis])
        except Exception:
            return False
        return True

    def plot_options(self):
        """
        define the settings for this, accepting any non-default values first
        """
        if len(self.axes) == 1:
            self.x_title() or self.set_x_title(self.axes[0])
            self.y_title() or self.set_y_title(self.signal)
        elif len(self.axes) == 2:
            self.x_title() or self.set_x_title(self.axes[1])
            self.y_title() or self.set_y_title(self.axes[0])
        self.x_log() or self.set_x_log(False)
        self.y_log() or self.set_y_log(False)
        self.z_log() or self.set_z_log(False)

    def retrieve_plot_data(self):
        """retrieve default data from spec data file

        data parser for 2-D mesh and hklmesh
        """
        (
            label1,
            _start1,
            _end1,
            intervals1,
            label2,
            _start2,
            _end2,
            intervals2,
            _time,
        ) = self.scan.scanCmd.split()[1:]
        if label1 not in self.scan.data:
            label1 = self.scan.L[0]  # mnemonic v. name
        if label2 not in self.scan.data:
            label2 = self.scan.L[1]  # mnemonic v. name
        axis1 = self.scan.data.get(label1)
        axis2 = self.scan.data.get(label2)
        intervals1, intervals2 = map(int, (intervals1, intervals2))
        # unused: start1, end1, start2, end2, time = map(float, (start1, end1, start2, end2, time))

        if len(axis1) < intervals1 and min(axis2) == max(axis2):
            # stopped scan before second row started, 1-D plot is better (issue #82)
            self.axes = [
                label1,
            ]
            self.signal = self.scan.column_last
            self.data[label1] = self.scan.data[label1]
            self.data[self.signal] = self.scan.data[self.signal]
            return

        axis1 = axis1[0 : intervals1 + 1]
        self.data[label1] = axis1  # 1-D array

        axis2 = [
            axis2[row]
            for row in range(len(axis2))
            if row % (intervals1 + 1) == 0
        ]
        self.data[label2] = axis2  # 1-D array

        column_labels = self.scan.L
        column_labels.remove(label1)  # special handling
        column_labels.remove(label2)  # special handling
        if self.scan.scanCmd.startswith("hkl"):
            # find the reciprocal space axis held constant
            label3 = [
                key for key in ("H", "K", "L") if key in column_labels
            ][0]
            self.data[label3] = self.scan.data.get(label3)[0]  # constant

        # build 2-D data objects (do not build label1, label2, [or label3] as 2-D objects)
        data_shape = [len(axis2), len(axis1)]
        for label in column_labels:
            if label not in self.data:
                axis = numpy.array(self.scan.data.get(label))
                self.data[label] = utils.reshape_data(axis, data_shape)
            else:
                pass

        self.signal = utils.clean_name(self.scan.column_last)
        self.axes = [label1, label2]

        if spec.MCA_DATA_KEY in self.scan.data:  # 3-D array(s)
            # save each spectrum
            for key, spectrum in sorted(
                self.scan.data[spec.MCA_DATA_KEY].items()
            ):
                num_channels = len(spectrum[0])
                data_shape.append(num_channels)
                mca = numpy.array(spectrum)
                data = utils.reshape_data(mca, data_shape)
                channels = range(1, num_channels + 1)
                ds_name = "_" + key + "_"
                self.data[ds_name] = data
                self.data[ds_name + "channel_"] = channels


# class NeXusPlotter(ImageMaker):    # TODO: issue #92
#     """
#     create a plot from a NeXus HDF5 data file
#     """
#
#     def retrieve_plot_data(self):
#         """retrieve default data from spec data file"""
#         raise NotImplementedError(self.__class__.__name__ + '() is not ready')
#
#     def make_image(self, plotFile):
#         """
#         make image file from the SPEC scan
#
#         :param str plotFile: name of image file to write
#         """
#         raise NotImplementedError(self.__class__.__name__ + '() is not ready')


def openSpecFile(specFile):
    """
    convenience routine so that others do not have to `import spec2nexus.spec`
    """
    sd = spec.SpecDataFile(specFile)
    return sd


def main():
    import argparse

    doc = __doc__.strip().splitlines()[0]
    p = argparse.ArgumentParser(description=doc)
    p.add_argument("specFile", help="SPEC data file name")
    p.add_argument(
        "scan_number", help="scan number in SPEC file", type=str
    )
    p.add_argument("plotFile", help="output plot file name")
    args = p.parse_args()

    sfile = openSpecFile(args.specFile)
    scan = sfile.getScan(args.scan_number)
    image_maker = Selector().auto(scan)
    plotter = image_maker()
    plotter.plot_scan(scan, args.plotFile)


if __name__ == "__main__":
    main()
