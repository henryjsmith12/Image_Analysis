"""
Copyright (c) UChicago Argonne, LLC. All rights reserved.
See LICENSE file.
"""

# ==============================================================================

import numpy as np
import os
from rsMap3D.config.rsmap3dconfigparser import RSMap3DConfigParser
from rsMap3D.datasource.Sector33SpecDataSource import Sector33SpecDataSource
from rsMap3D.datasource.DetectorGeometryForXrayutilitiesReader import DetectorGeometryForXrayutilitiesReader as detReader
from rsMap3D.datasource.InstForXrayutilitiesReader import InstForXrayutilitiesReader as instrReader
from rsMap3D.gui.rsm3dcommonstrings import BINARY_OUTPUT
from rsMap3D.mappers.gridmapper import QGridMapper
from rsMap3D.mappers.output.vtigridwriter import VTIGridWriter
from rsMap3D.transforms.unitytransform3d import UnityTransform3D
from rsMap3D.utils.srange import srange
import vtk
from vtk.util import numpy_support as npSup
import xrayutilities as xu

# ==============================================================================

class DataProcessing:

    """
    Various functions to convert, read, and process data before displaying.
    """

    def createVTIFile(project_dir, spec_file, detector_config_name, instrument_config_name,
        scan, nx, ny, nz):

        """
        Creates a .vti file which can be read by VTK and converted into an array.
        """

        # Necessary subfunctions for function to run smoothly
        # See rsMap3D source code
        def updateDataSourceProgress(value1, value2):
            print("DataSource Progress %s/%s" % (value1, value2))

        def updateMapperProgress(value1):
            print("Mapper Progress %s" % (value1))

        d_reader = detReader(detector_config_name)
        detector_name = "Pilatus"
        detector = d_reader.getDetectorById(detector_name)
        n_pixels = d_reader.getNpixels(detector)
        roi = [1, n_pixels[0], 1, n_pixels[1]]
        bin = [1,1]

        spec_name, spec_ext = os.path.splitext(os.path.basename(spec_file))
        # Set destination file for gridmapper
        output_file_name = os.path.join(project_dir, spec_name + "_" + scan + ".vti")

        if os.path.exists(output_file_name):
            return output_file_name

        app_config = RSMap3DConfigParser()
        max_image_memory = app_config.getMaxImageMemory()

        scan_range = srange(scan).list()
        data_source = Sector33SpecDataSource(project_dir, spec_name, spec_ext,
            instrument_config_name, detector_config_name, roi=roi, pixelsToAverage=bin,
            scanList=scan_range, appConfig=app_config)
        data_source.setCurrentDetector(detector_name)
        data_source.setProgressUpdater(updateDataSourceProgress)
        data_source.loadSource(mapHKL=True)
        data_source.setRangeBounds(data_source.getOverallRanges())
        image_tbu = data_source.getImageToBeUsed()
        image_size = np.prod(data_source.getDetectorDimensions())

        grid_mapper = QGridMapper(data_source, output_file_name, nx=nx, ny=ny, nz=nz,
            outputType=BINARY_OUTPUT, transform=UnityTransform3D(),
            gridWriter=VTIGridWriter(), appConfig=app_config)
        grid_mapper.setProgressUpdater(updateMapperProgress)
        grid_mapper.doMap()

        return output_file_name

    # --------------------------------------------------------------------------

    def loadData(vti_file):

        """
        Converts information from .vti file into an array in HKL.
        """

        reader = vtk.vtkXMLImageDataReader()
        reader.SetFileName(vti_file)
        reader.Update()

        data = reader.GetOutput()
        dim = data.GetDimensions()

        vec = list(dim)

        vec = [i for i in dim]
        vec.reverse()

        u = npSup.vtk_to_numpy(data.GetPointData().GetArray('Scalars_'))

        max_value = np.nanmax(u)
        min_value = np.nanmin(u)

        u = u.reshape(vec)

        # Swaps H and L
        ctrdata = np.swapaxes(u, 0, 2)

        origin = data.GetOrigin()
        spacing = data.GetSpacing()
        extent = data.GetExtent()

        x = []
        y = []
        z = []

        for point in range(extent[0], extent[1] + 1):
            x.append(origin[0] + point * spacing[0])
        for point in range(extent[2], extent[3] + 1):
            y.append(origin[1] + point * spacing[1])
        for point in range(extent[4], extent[5] + 1):
            z.append(origin[2] + point * spacing[2])

        axes = [x, y, z]

        return axes, ctrdata

    # --------------------------------------------------------------------------

    def createLiveScanArea(detector_config_name, instrument_config_name, mu, eta,
        chi, phi, nu, delta, ub, energy):

        d_reader = detReader(detector_config_name)
        i_reader = instrReader(instrument_config_name)

        sample_circle_dir = i_reader.getSampleCircleDirections()
        det_circle_dir = i_reader.getDetectorCircleDirections()
        primary_beam_dir = i_reader.getPrimaryBeamDirection()

        q_conv = xu.experiment.QConversion(sample_circle_dir, det_circle_dir, primary_beam_dir)

        inplane_ref_dir = i_reader.getInplaneReferenceDirection()
        sample_norm_dir = i_reader.getSampleSurfaceNormalDirection()

        hxrd = xu.HXRD(inplane_ref_dir, sample_norm_dir, en=energy, qconv=q_conv)

        detector = d_reader.getDetectors()[0]
        pixel_dir_1 = d_reader.getPixelDirection1(detector)
        pixel_dir_2 = d_reader.getPixelDirection2(detector)
        c_ch_1 = d_reader.getCenterChannelPixel(detector)[0]
        c_ch_2 = d_reader.getCenterChannelPixel(detector)[1]
        n_ch_1 = d_reader.getNpixels(detector)[0]
        n_ch_2 = d_reader.getNpixels(detector)[1]
        pixel_width_1 = d_reader.getSize(detector)[0] / d_reader.getNpixels(detector)[0]
        pixel_width_2 = d_reader.getSize(detector)[1] / d_reader.getNpixels(detector)[1]
        distance = d_reader.getDistance(detector)
        roi = [0, n_ch_1, 0, n_ch_2]

        hxrd.Ang2Q.init_area(pixel_dir_1, pixel_dir_2, cch1=c_ch_1, cch2=c_ch_2,
            Nch1=n_ch_1, Nch2=n_ch_2, pwidth1=pixel_width_1, pwidth2=pixel_width_2,
            distance=distance, roi=roi)

        qx,qy,qz = hxrd.Ang2Q.area(mu,eta,chi,phi,nu,delta,UB=ub)

        return qx, qy, qz

# ==============================================================================
