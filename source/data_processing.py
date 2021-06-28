"""
Copyright (c) UChicago Argonne, LLC. All rights reserved.
See LICENSE file.
"""

# ==============================================================================

import numpy as np
import os
from rsMap3D.datasource.Sector33SpecDataSource import Sector33SpecDataSource
from rsMap3D.datasource.DetectorGeometryForXrayutilitiesReader import DetectorGeometryForXrayutilitiesReader as detReader
from rsMap3D.utils.srange import srange
from rsMap3D.config.rsmap3dconfigparser import RSMap3DConfigParser
from rsMap3D.constants import ENERGY_WAVELENGTH_CONVERT_FACTOR
from rsMap3D.mappers.gridmapper import QGridMapper
from rsMap3D.gui.rsm3dcommonstrings import BINARY_OUTPUT
from rsMap3D.transforms.unitytransform3d import UnityTransform3D
from rsMap3D.mappers.output.vtigridwriter import VTIGridWriter
import vtk
from vtk.util import numpy_support as npSup
import xrayutilities as xu


# ==============================================================================

class DataProcessing:

    def createVTIFile(project_dir, spec_file, detector_config_name, instrument_config_name, scan):
        d_reader = detReader(detector_config_name)
        detector_name = "Pilatus"
        detector = d_reader.getDetectorById(detector_name)
        n_pixels = d_reader.getNpixels(detector)
        roi = [1, n_pixels[0], 1, n_pixels[1]]
        bin = [1,1]

        spec_name, spec_ext = os.path.splitext(os.path.basename(spec_file))
        output_file_name = os.path.join(project_dir, spec_name + '.vti')

        app_config = RSMap3DConfigParser()
        max_image_memory = app_config.getMaxImageMemory()

        scan_range = srange(scan).list()
        data_source = Sector33SpecDataSource(project_dir, spec_name, spec_ext,
            instrument_config_name, detector_config_name, roi=roi, pixelsToAverage=bin,
            scanList= scan_range, appConfig=app_config)

        data_source.setCurrentDetector(detector_name)
        data_source.loadSource(mapHKL=True)
        data_source.setRangeBounds(data_source.getOverallRanges())
        image_tbu = data_source.getImageToBeUsed()
        image_size = np.prod(data_source.getDetectorDimensions())

        grid_mapper = QGridMapper(data_source, output_file_name, outputType=BINARY_OUTPUT,
            transform=UnityTransform3D(), gridWriter=VTIGridWriter(), appConfig=app_config)

        try:
            grid_mapper.doMap()
        except TypeError:
            ...

        return output_file_name

    # --------------------------------------------------------------------------

    def loadData(vti_file):
        reader = vtk.vtkXMLImageDataReader()
        reader.SetFileName(vti_file)
        reader.Update()

        data = reader.GetOutput()
        vectors = list(data.GetDimensions())

        u = npSup.vtk_to_numpy(data.GetPointData().GetArray('Scalars_'))

        max_value = np.nanmax(u)
        min_value = np.nanmin(u)

        u = u.reshape(vectors)

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

        print ("H (" + str(x[0]) + ", " + str(x[-1]) + ")")
        print ("K (" + str(y[0]) + ", " + str(y[-1]) + ")")
        print ("L (" + str(z[0]) + ", " + str(z[-1]) + ")")
        
        axes = [x, y, z]

        return axes, ctrdata


# ==============================================================================
