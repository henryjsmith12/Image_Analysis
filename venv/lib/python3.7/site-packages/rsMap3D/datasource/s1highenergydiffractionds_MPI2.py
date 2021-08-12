'''
 Copyright (c) 2017 UChicago Argonne, LLC
 See LICENSE file.
'''
import logging
import time
import numpy as np

import xrayutilities as xu
from rsMap3D.config.rsmap3dlogging import METHOD_ENTER_STR, METHOD_EXIT_STR
from rsMap3D.mappers.abstractmapper import ProcessCanceledException
import sys

from rsMap3D.datasource.AbstractXrayUtilitiesDataSource \
    import AbstractXrayutilitiesDataSource
import rsMap3D.datasource.InstForXrayutilitiesReader \
    as InstReader
import rsMap3D.datasource.DetectorGeometryForXrayutilitiesReader \
    as DetectorReader
from rsMap3D.exception.rsmap3dexception import InstConfigException,\
    RSMap3DException, DetectorConfigException
from mpi4py import MPI
import os

logger = logging.getLogger(__name__)
FIRST_COL = "weekdate"
S1_MOTOR = "s1_motname"
S1_START_POS = "s1_startpos"
S1_END_POS = "s1_endpos"
NFRAMES = 'OSC["nframes"]'
IMAGE_PREFIX = "imgprefix"
IMAGE_NUMBER = "imgnr"
S2_MOTOR = "s2_motname"
D1_MOTOR = "d1_motname"
S2_START_POS = "s2_startpos"
D1_START_POS = "d1_startpos"
S2_END_POS = "s2_endpos"
D1_END_POS = "d1_endpos" 
INCIDENT_ENERGY = "Energy(keV)"
FILE_EXT = "file_ext"
BYTES_PER_PIXEL = 4

KEV_TO_EV = 1000

EXPECTED_COLUMNS = {FIRST_COL, S1_MOTOR,S1_START_POS, NFRAMES,
                    IMAGE_PREFIX, IMAGE_NUMBER, S2_MOTOR, S2_START_POS,
                    D1_MOTOR, D1_START_POS}

def divideImages(imageList, mpiSize):
    numImages, remaining = divmod(len(imageList), mpiSize)
    dividedGen = (imageList[i*numImages + min(i, remaining):
                     (i+1) * numImages + min(i+1, remaining)]
            for i in xrange(mpiSize))
    return list(dividedGen)

class S1HighEnergyDiffractionDS(AbstractXrayutilitiesDataSource):
    '''
    '''
    
    def __init__(self, 
                 projectDir,
                 projectName,
                 projectExtension,
                 instConfigFile,
                 detConfigFile,
                 imageDirName,
                 detectorId="GE",
                 detectorDistanceOverride=0.0,
                 incidentEnergyOverride=0.0,
                 offsetAngle=0.0,
                 **kwargs):
        super(S1HighEnergyDiffractionDS, self).__init__(**kwargs)
        logger.debug(METHOD_ENTER_STR)
        self.projectDir = str(projectDir)
        self.projectName = str(projectName)
        self.projectExtension = str(projectExtension)
        self.instConfigFile = str(instConfigFile)
        self.detConfigFile = str(detConfigFile)
        self.imageDirName = str(imageDirName)
        self.detectorId = detectorId
        self.detectorDistanceOverride = detectorDistanceOverride
        self.incidentEnergyOverride = incidentEnergyOverride
        self.offsetAngle = offsetAngle
        try:
            self.scans = kwargs['scanList']
        except KeyError:
            self.scans = None
        self.files = None
        self.availableFiles = []
#        self.detectorROI = []
        self.incidentEnergy = {}
        self.progressUpdater = None
        self.progress = 0
        self.progressInc = 1.0 *100.0
        self.progressMax = 1
        self.cancelLoad = False
        self.haltMap = False
        
        self.currentDetector = detectorId
        logger.debug(METHOD_EXIT_STR)

    #@profile
    def findImageQs(self, angles, ub, en):
        logger.debug(METHOD_ENTER_STR)

        # Initialize communicator for this part of the work
#        comm = MPI.COMM_WORLD
        hostFile = self.appConfig.getMPIWorkerHostFile()
        workerCount = self.appConfig.getMPIWorkerCount()
        
        mpi_info = MPI.Info.Create()
        mpi_info.Set("add-hostfile", hostFile)
        
#         rank = comm.Get_rank()
#         size = comm.Get_size()
        
        processorHost = MPI.Get_processor_name()
#         logger.debug( "MPI Master world size %d, rank %d host %s" %
#                       (size, rank, processorHost))
        
        # set up process name to spawn
        logger.debug("Sys.executable %s" % str(sys.executable))
        logger.debug("__file__ %s " % str(__file__))
        selfPath = os.path.dirname(__file__)
        clientName = os.path.join(selfPath, 's1mpiclient.py')
        # HERE IS WHERE WE ACTUALLY SPAWN A BUNCH OF PROCESSES.
        comm_work = MPI.COMM_WORLD.Spawn(
            sys.executable,
            args=[clientName, 'findImageQs'],
            maxprocs = workerCount)
        rank = comm_work.Get_rank()
        size = comm_work.Get_size()
        
        processorHost = MPI.Get_processor_name()
        logger.debug( "MPI Master world size %d, rank %d host %s" %
                      (size, rank, processorHost))
        # Setup to send out data needed for QConversion 
        directions = {"sampleCircleDirections" : self.sampleCircleDirections,
                      "detectorCircleDirections" : self.detectorCircleDirections,
                      "primaryBeamDirection" : self.primaryBeamDirection}
        directions = comm_work.bcast(directions, root = MPI.ROOT)
        comm_work.Barrier()
        logger.debug("sampleCircleDirections: " + \
                     str(self.sampleCircleDirections))
        logger.debug("detectorCircleDirections: " + \
                     str(self.detectorCircleDirections))
        logger.debug("primaryBeamDirection: " + \
                     str(self.primaryBeamDirection))
        
        # Send out data to workes to do HXRD
        HXRD_args = {"en" : en,
                    "inplaneRef" : self.sampleInplaneReferenceDirection,
                    "sampleNorm" : self.sampleSurfaceNormalDirection}
        logger.debug("en: " + str(en))
        logger.debug("inplaneReferenceDirection: " + \
                     str(self.sampleInplaneReferenceDirection))
        logger.debug("sampleSurfaceNormalDirection: " + \
                     str(self.sampleSurfaceNormalDirection))
        HXRD_args = comm_work.bcast(HXRD_args, root = MPI.ROOT)
        comm_work.Barrier()

        # Send out parameters needed for init_area.        
        cch = self.detectorCenterChannel
        nav = self.numPixelsToAverage
        roi = self.detectorROI
        detDims = self.detectorDimensions
        
        logger.debug("pixelDirections: " + 
                     str((self.detectorPixelDirection1, 
                          self.detectorPixelDirection2)))
        logger.debug("distance to detector %f, pixel Size %s" % \
                     (self.distanceToDetector, str(self.detectorPixelWidth)))
        if self.detectorDistanceOverride == 0.0:
            detectorDistance = self.distanceToDetector
        else:
            detectorDistance = self.detectorDistanceOverride
            
        init_area_args = {"pixDir1" : self.getDetectorPixelDirection1(),
                          "pixDir2" : self.getDetectorPixelDirection2(),
                          "cch" : cch,
                          "detDims" : detDims,
                          "pixWidth" : self.detectorPixelWidth,
                          "distance" : detectorDistance,
                          "Nav" : nav,
                          "roi" : roi}
        init_area_args = comm_work.bcast(init_area_args, root=MPI.ROOT)
        comm_work.Barrier()

        
        #---- Feed image Info for calculating the q's, numImages, imageSize, etc
        maxImageMem = self.appConfig.getMaxImageMemory()
        imageSize = detDims[0] * detDims[1]
        numImages = len(angles)
        imageInfo = {'imageSize' : imageSize,
                      'numImages' : numImages,
                      'bytesPerPixel' : BYTES_PER_PIXEL,
                      'maxImageMem'  : maxImageMem,
                      'ub' : ub,
                      'transform' :self.transform}
        imageInfo = comm_work.bcast(imageInfo, root = MPI.ROOT)
        comm_work.Barrier()
        if imageSize*BYTES_PER_PIXEL*numImages <= maxImageMem:
            self.progressMax = len( self.scans) * 100
            self.progressInc = 1.0 * 100.0
            if self.progressUpdater <> None:
                self.progressUpdater(self.progress, self.progressMax)
            self.progress += self.progressInc        
            angleList = []
            for i in range(len(angles[0])):
                angleList.append(angles[:,i])
            if ub is None:
                qx, qy, qz = hxrd.Ang2Q.area(*angleList, \
                                         roi=roi, \
                                         Nav=nav)
            else:
                qx, qy, qz = hxrd.Ang2Q.area(*angleList, \
                                         roi=roi, \
                                         Nav=nav, \
                                         UB = ub)
                 
            logger.debug("Before transform qx, qy, qz " + str((qx,qy,qz)))     
            qxTrans, qyTrans, qzTrans = self.transform.do3DTransform(qx, qy, qz)
            logger.debug("After transform qx, qy, qz " + 
                         str((qxTrans,qyTrans,qzTrans)))     
            
            idx = range(len(qxTrans))
            xmin = [np.min(qxTrans[i]) for i in idx] 
            xmax = [np.max(qxTrans[i]) for i in idx] 
            ymin = [np.min(qyTrans[i]) for i in idx] 
            ymax = [np.max(qyTrans[i]) for i in idx] 
            zmin = [np.min(qzTrans[i]) for i in idx] 
            zmax = [np.max(qzTrans[i]) for i in idx] 
        else:
            nPasses = imageSize*4*numImages/ maxImageMem + 1
            xmin = []
            xmax = []
            ymin = []
            ymax = []
            zmin = []
            zmax = []
            for thisPass in range(nPasses):
                self.progressMax = len( self.scans) * 100.0
                self.progressInc = 1.0 / nPasses * 100.0
                if self.progressUpdater <> None:
                    self.progressUpdater(self.progress, self.progressMax)
                self.progress += self.progressInc        
                firstImageInPass = thisPass*numImages/nPasses
                lastImageInPass = (thisPass+1)*numImages/nPasses
                logger.debug("firstImageInPass %d, lastImageInPass %d" %
                             (firstImageInPass, lastImageInPass))
                imageList = list(xrange(firstImageInPass, lastImageInPass))
                angleList = []
                #logger.debug("angles " + str(angles) )
                size = comm_work.Get_size()
                logger.debug( "ImageList %s, size %d " % (imageList, workerCount))
                dividedImages = divideImages(imageList, workerCount)
                logger.debug("dividedImages %s" % str(dividedImages))
                area_args = {'dividedImages' : dividedImages,
                             'angles' : angles}
                comm_work.bcast(area_args, root=MPI.ROOT)
                comm_work.Barrier()
                # AT THIS POINT CLIENTS WILL DO hxrd.Ang2Q.area
                # Gather results from the Ranks
                for procRank in xrange(workerCount):
                    rangeShape = np.empty((2,), dtype=int)
                    comm_work.Recv(rangeShape, source=procRank)
                    logger.debug("Master procRank %d rangeShape %s" % (procRank,
                                                                       rangeShape))
                    logger.debug (tuple(rangeShape))
                    rangeData = np.empty(tuple(rangeShape))
                    logger.debug("Master procRank %d Waiting to receive" % procRank)
                    comm_work.Recv(rangeData, source=procRank)
                    logger.debug("Master procRank %d rangeData %s" % (procRank,
                                                                       rangeData))
                    
                    xmin.extend(list(rangeData[0]))
                    xmax.extend(list(rangeData[1]))
                    ymin.extend(list(rangeData[2]))
                    ymax.extend(list(rangeData[3]))
                    zmin.extend(list(rangeData[4]))
                    zmax.extend(list(rangeData[5]))
                comm_work.Barrier()
                idx = range(len(rangeData[0]))
                # Using Maps
#                 xmin.extend(map(np.min, qxTrans))
#                 xmax.extend(map(np.max, qxTrans))
#                 ymin.extend(map(np.min, qyTrans))
#                 ymax.extend(map(np.max, qyTrans))
#                 zmin.extend(map(np.min, qzTrans))
#                 zmax.extend(map(np.max, qzTrans))

                ####
        comm_work.Disconnect()
        logger.debug(METHOD_EXIT_STR + str((xmin, xmax, ymin, ymax, zmin, zmax)) ) 
        return (xmin, xmax, ymin, ymax, zmin, zmax)
    
    def getGeoAngles(self, scan): 
        angles = np.ones((self.angleParams[scan][NFRAMES], 3))
        logger.debug(METHOD_ENTER_STR)
        logger.debug("self.angleParams " + str(self.angleParams))
        logger.debug("self.angleParams[%d] : %s" % (scan, str(self.angleParams[scan])))
        
        s1Angles = np.ones(self.angleParams[scan][NFRAMES])
        s2Angles = np.ones(self.angleParams[scan][NFRAMES])
        d1Angles = np.ones(self.angleParams[scan][NFRAMES])
        if self.angleParams[scan][S1_START_POS] != \
            self.angleParams[scan][S1_END_POS]:
            stepSize = (self.angleParams[scan][S1_END_POS] - \
                        self.angleParams[scan][S1_START_POS]) / \
                        self.angleParams[scan][NFRAMES]
            logger.debug("range %s " % str(len(range(0,self.angleParams[scan][NFRAMES]))) )
            for frame in range(0,self.angleParams[scan][NFRAMES]):
                s1Angles[frame] = self.angleParams[scan][S1_START_POS] + \
                                frame * stepSize
        else:
            s1Angles = s1Angles * self.angleParams[scan][S1_START_POS]

        if self.angleParams[scan][S2_START_POS] != \
            self.angleParams[scan][S2_END_POS]:
            stepSize = (self.angleParams[scan][S2_END_POS] - \
                         self.angleParams[scan][S2_START_POS])/ \
                         self.angleParams[scan][NFRAMES]
            for frame in range(0, self.angleParams[scan][NFRAMES]):
                s2Angles[frame] = self.angleParams[scan][S2_START_POS] + \
                    frame * stepSize
        else:
            s2Angles = s2Angles * self.angleParams[scan][S2_START_POS]

        if self.angleParams[scan][D1_START_POS] != \
            self.angleParams[scan][D1_END_POS]:
            stepSize = (self.angleParams[scan][D1_END_POS] - \
                         self.angleParams[scan][D1_START_POS])/ \
                         self.angleParams[scan][NFRAMES]
            for frame in range(0, self.angleParams[scan][NFRAMES]):
                d1Angles[frame] = self.angleParams[scan][D1_START_POS] + \
                            frame * stepSize
        else:
            d1Angles = d1Angles * self.angleParams[scan][D1_START_POS]
#            angles.append([s1Angle, s2Angle, d1Angle])
        angles[:,0] = s1Angles
        angles[:,1] = s2Angles
        angles[:,2] = d1Angles
        logger.debug(METHOD_EXIT_STR % "\n" + str(angles))
        return angles
                
    def getReferenceNames(self):
        names = []
        names.append(self.angleParams[self.availableScans[0]][S1_MOTOR])
        names.append(self.angleParams[self.availableScans[0]][S2_MOTOR])
        names.append(self.angleParams[self.availableScans[0]][D1_MOTOR])
        return names
    
    def getReferenceValues(self,scan):
        angles = self.getGeoAngles(scan)
        return angles
    
    def loadDetectorXMLConfig(self):
        logger.debug(METHOD_ENTER_STR)
        try:
            detConfig = \
                DetectorReader.DetectorGeometryForXrayutilitiesReader(
                                                      self.detConfigFile)
            detector = detConfig.getDetectorById(self.currentDetector)
            self.detectorCenterChannel = \
                detConfig.getCenterChannelPixel(detector)
            self.detectorDimensions = detConfig.getNpixels(detector)
            detectorSize = detConfig.getSize(detector)
            self.detectorPixelWidth = \
                [detectorSize[0]/self.detectorDimensions[0],\
                 detectorSize[1]/self.detectorDimensions[1]]
            self.distanceToDetector = detConfig.getDistance(detector) 
            if self.numPixelsToAverage is None:
                self.numPixelsToAverage = [1,1]
            if self.detectorROI is None:
                self.detectorROI = [0, self.detectorDimensions[0],  
                                    0, self.detectorDimensions[1]]
            self.detectorPixelDirection1 = \
                detConfig.getPixelDirection1(detector)
            self.detectorPixelDirection2 = \
                detConfig.getPixelDirection2(detector)
        except DetectorConfigException as ex:
            raise ex
        except RSMap3DException as ex:
            raise ex
        except Exception as ex:
            logger.exeption ("---Unhandled Exception in loading detector config")
            raise ex
        logger.debug(METHOD_EXIT_STR)
        
    def loadInstrumentXMLConfig(self):
        logger.debug(METHOD_ENTER_STR)
        try:
            self.instConfig = \
                InstReader.InstForXrayutilitiesReader(self.instConfigFile)
            self.sampleCircleDirections = \
                self.instConfig.getSampleCircleDirections()
            self.detectorCircleDirections = \
                self.instConfig.getDetectorCircleDirections()
            self.primaryBeamDirection = \
                self.instConfig.getPrimaryBeamDirection()
            self.sampleInplaneReferenceDirection = \
                self.instConfig.getInplaneReferenceDirection()
            self.sampleSurfaceNormalDirection = \
                self.instConfig.getSampleSurfaceNormalDirection()
            self.sampleAngleNames = self.instConfig.getSampleCircleNames()
            self.detectorAngleNames = self.instConfig.getDetectorCircleNames()
            self.monitorName = self.instConfig.getMonitorName()
            self.monitorScaleFactor = self.instConfig.getMonitorScaleFactor()
            self.filterName = self.instConfig.getFilterName()
            self.filterScaleFactor = self.instConfig.getFilterScaleFactor()
            self.angleNames = self.instConfig.getSampleCircleNames() + \
                self.instConfig.getDetectorCircleNames()
            self.projectionDirection = self.instConfig.getProjectionDirection()
        except InstConfigException as ex:
            raise ex
        except RSMap3DException as ex:
            raise ex
        except Exception as ex:
            logger.error( "Unhandle Exception loading instrument config" + 
                           str(ex))
            raise ex
        logger.debug(METHOD_EXIT_STR)

    def loadSource(self, mapHKL=False):
        '''
        This method does the work of loading data from files..
        
        '''
        logger.debug(METHOD_ENTER_STR)
        # Load up the instrument configuration File
        self.loadInstrumentXMLConfig()
        # Load up the detector configuration file.
        self.loadDetectorXMLConfig()
        
        self.parFileName = os.path.join(self.projectDir, \
                                        self.projectName + \
                                        self.projectExtension)
        self.parFile = S1ParameterFile(self.parFileName)
        
        self.angleParams = self.parFile.getAngleData(self.scans)
        angles = None
        self.imageBounds = {}
        self.imageToBeUsed = {}
        self.availableScans = []
        self.incidentEnergy = {}
        self.ubMatrix = {}
        self.scanType = {}
        self.progress = 0
        self.progressInc = 1
        self.mapHKL = mapHKL

        for scan in self.scans:
            self.ubMatrix[scan] = None
            self.scanType[scan] = "ascan"
            angles = self.getGeoAngles(scan)
            self.availableScans.append(scan)
            #TODO
            if self.mapHKL==True:
                self.ubMatrix[scan] = self.getUBMatrix(scan)
                if self.ubMatrix[scan] is None:
                    raise RSMap3DException("UB matrix " + \
                                                        "not found.")
                else:
                    self.ubMatrix[scan] = None
            
            
            #TODO
            energyData = self.parFile.getEnergy([scan,])
            logger.debug("energyData " + str(energyData))

            #if self.incidentEnergyOverride == 0.0:            
            self.incidentEnergy[scan] = \
                energyData[scan][INCIDENT_ENERGY] * KEV_TO_EV
            #else:
            logging.debug("energyData[scan]: " + str(self.incidentEnergy[scan]))     
            _start_time = time.time()
            self.imageBounds[scan] = \
                self.findImageQs(angles, \
                                 self.ubMatrix[scan], \
                                 self.incidentEnergy[scan])
            
        
        
        self.fileParams = self.parFile.getFileData(self.scans)
        logger.debug(METHOD_EXIT_STR)
        
        
    #@profile
    def rawmap(self, scans, angledelta=[0,0,0,0],
               adframes=None, mask=None ):
        logger.debug(METHOD_ENTER_STR)
        if mask is None:
            mask_was_none = True
        else:
            mask_was_none = False
            
        intensity = np.array([])
        
        processorHost = MPI.Get_processor_name()

        # set up process name to spawn
        logger.debug("Sys.executable %s" % str(sys.executable))
        logger.debug("__file__ %s " % str(__file__))
        selfPath = os.path.dirname(__file__)
        clientName = os.path.join(selfPath, 's1mpiclient.py')
        # HERE IS WHERE WE ACTUALLY SPAWN A BUNCH OF PROCESSES.
        workerCount = self.appConfig.getMPIWorkerCount()
        comm_work = MPI.COMM_WORLD.Spawn(
            sys.executable,
            args=[clientName, 'rawmap'],
            maxprocs = workerCount)

        rank = comm_work.Get_rank()
        size = comm_work.Get_size()          
        logger.debug( "MPI Master world size %d, rank %d host %s" %
                      (size, rank, processorHost))
        # Setup to send out data needed for QConversion 
        directions = {"sampleCircleDirections" : self.sampleCircleDirections,
                      "detectorCircleDirections" : self.detectorCircleDirections,
                      "primaryBeamDirection" : self.primaryBeamDirection}
        directions = comm_work.bcast(directions, root = MPI.ROOT)
        comm_work.Barrier()
        logger.debug("sampleCircleDirections: " + \
                     str(self.sampleCircleDirections))
        logger.debug("detectorCircleDirections: " + \
                     str(self.detectorCircleDirections))
        logger.debug("primaryBeamDirection: " + \
                     str(self.primaryBeamDirection))
        

#         qconv = xu.experiment.QConversion(self.sampleCircleDirections, \
#                                     self.detectorCircleDirections, \
#                                     self.primaryBeamDirection)
    

#         # initialize area detector properties
#         if (self.detectorPixelWidth != None ) and \
#             (self.distanceToDetector != None):
#             hxrd.Ang2Q.init_area(self.detectorPixelDirection1, \
#                 self.detectorPixelDirection2, \
#                 cch1=self.detectorCenterChannel[0], \
#                 cch2=self.detectorCenterChannel[1], \
#                 Nch1=self.detectorDimensions[0], \
#                 Nch2=self.detectorDimensions[1], \
#                 pwidth1=self.detectorPixelWidth[0], \
#                 pwidth2=self.detectorPixelWidth[1], \
#                 distance=self.distanceToDetector, \
#                 Nav=self.numPixelsToAverage, \
#                 roi=self.detectorROI) 
#         else:
#             hxrd.Ang2Q.init_area(self.detectorPixelDirection1, \
#                 self.detectorPixelDirection2, \
#                 cch1=self.detectorCenterChannel[0], \
#                 cch2=self.detectorCenterChannel[1], \
#                 Nch1=self.detectorDimensions[0], \
#                 Nch2=self.getDetectorDimensions[1], \
#                 chpdeg1=self.detectorChannelsPerDegree[0], \
#                 chpdeg2=self.detectorChannelsPerDegree[1], \
#                 Nav=self.numPixelsToAverage, 
#                 roi=self.detectorROI) 
        
        angleNames = self.getAngles()
        scanAngle = {}
        for i in xrange(len(angleNames)):
            scanAngle[i] = np.array([])
        
        offset = 0
        imageToBeUsed = self.imageToBeUsed
        logger.debug("Master scans: %s" % str(scans))
        logger.debug("Master imageToBeUsed: %s" % str(imageToBeUsed))
        logger.debug("Master angleNames: %s" % str(angleNames))
#         scanInfo = {'scans' : scans, \
#                     'angleNames': angleNames}
#         
#         scanInfo = comm_work.bcast(scanInfo, root=MPI.ROOT)
#         comm_work.Barrier()
        tImageToBeUsed = imageToBeUsed
        tScans = scans
        tAngleNames = angleNames        
        comm_work.bcast(tScans, root=MPI.ROOT, )
        comm_work.Barrier()
        comm_work.bcast(tAngleNames, root=MPI.ROOT)
        comm_work.Barrier()
        comm_work.bcast(tImageToBeUsed, root=MPI.ROOT)
        comm_work.Barrier()
        logger.debug("Master scans: %s" % str(scans))
        logger.debug("Master imageToBeUsed: %s" % str(imageToBeUsed))
        logger.debug("Master angleNames: %s" % str(angleNames))
        for scannr in scans:
            comm_work.bcast(self.haltMap, root=MPI.ROOT)
            comm_work.Barrier()
            if self.haltMap:
                comm_work.Disconnect()
                raise ProcessCanceledException("ProcessCanceled")
            en = self.incidentEnergy[scannr]
            HXRD_args = {"en" : en,
                        "inplaneRef" : self.sampleInplaneReferenceDirection,
                        "sampleNorm" : self.sampleSurfaceNormalDirection}
            logger.debug("en: " + str(en))
            logger.debug("inplaneReferenceDirection: " + \
                         str(self.sampleInplaneReferenceDirection))
            logger.debug("sampleSurfaceNormalDirection: " + \
                         str(self.sampleSurfaceNormalDirection))
            HXRD_args = comm_work.bcast(HXRD_args, root = MPI.ROOT)
            comm_work.Barrier()
    
    #         hxrd = xu.HXRD(self.sampleInplaneReferenceDirection, \
    #                        self.sampleSurfaceNormalDirection, \
    #                        en=en[self.availableScans[0]], \
    #                        qconv=qconv)
           
            # Send out parameters needed for init_area.        
            cch = self.detectorCenterChannel
            nav = self.numPixelsToAverage
            roi = self.detectorROI
            detDims = self.detectorDimensions
            
            logger.debug("pixelDirections: " + 
                         str((self.detectorPixelDirection1, 
                              self.detectorPixelDirection2)))
            logger.debug("distance to detector %f, pixel Size %s" % \
                         (self.distanceToDetector, str(self.detectorPixelWidth)))
            if self.detectorDistanceOverride == 0.0:
                detectorDistance = self.distanceToDetector
            else:
                detectorDistance = self.detectorDistanceOverride
                
            initAreaArgs = {"pixDir1" : self.getDetectorPixelDirection1(),
                              "pixDir2" : self.getDetectorPixelDirection2(),
                              "cch" : cch,
                              "detDims" : detDims,
                              "pixWidth" : self.detectorPixelWidth,
                              "distance" : detectorDistance,
                              "Nav" : nav,
                              "roi" : roi,
                              'transform' : self.transform}
            initAreaArgs = comm_work.bcast(initAreaArgs, root=MPI.ROOT)
            comm_work.Barrier()
            angles = self.getGeoAngles(scannr)

            #---- Feed image Info for calculating the q's, numImages, imageSize, etc
            maxImageMem = self.appConfig.getMaxImageMemory()
            imageSize = detDims[0] * detDims[1]
            numImages = len(angles)
            imageInfo = {'imageSize' : imageSize,
                          'numImages' : numImages,
                          'bytesPerPixel' : BYTES_PER_PIXEL,
                          'maxImageMem'  : maxImageMem,
                          'ub' : self.ubMatrix[scannr],
                          'transform' :self.transform}
            imageInfo = comm_work.bcast(imageInfo, root = MPI.ROOT)
            comm_work.Barrier()
            
#            imageList = list(xrange(len(angles[:,0])))
            logger.debug("******imageToBeUsed %s" % str(imageToBeUsed))
            logger.debug("******mask %s " % str(mask))
            imageList = np.where(np.array(mask))[0]
            logger.debug("******imageList %s " % str(imageList))
            dividedList = divideImages(imageList, workerCount)
            dividedImages = { 'dividedList' : dividedList,
                            'angles' : angles}
            comm_work.bcast(dividedImages, root=MPI.ROOT)
            comm_work.Barrier()

            logger.debug("angles in scan %d: %s" % (scannr, angles))
            scanAngle1 = {}
            scanAngle2 = {}
            for i in xrange(len(angleNames)):
                scanAngle1[i] = angles[:,i]
                scanAngle2[i] = []
            arrayInitializedForScan = False
            foundIndex = 0
#             logger.debug("imageDirName %s" %  self.imageDirName)
#             logger.debug(("fileParams[%d]" % scannr) + str(self.fileParams[scannr]))
            imageFilePrefix = os.path.join(self.imageDirName,
                                      self.fileParams[scannr][IMAGE_PREFIX] +
                                      "_" +
                                      self.fileParams[scannr][IMAGE_NUMBER] +
                                      "." +
                                      self.fileParams[scannr][FILE_EXT])
            imageNameTemplate = str(imageFilePrefix) +'.frame%d.cor'
            
            if mask_was_none:
                mask = [True] * len(self.imageToBeUsed[scannr])
            imageFileInfo = {"imageNameTemplate" : imageNameTemplate,
                             'mask' : mask}
            comm_work.bcast(imageFileInfo, root=MPI.ROOT)
            comm_work.Barrier()
            
            logger.debug("imageToBeUsed" + str(imageToBeUsed))
            logger.debug("mask" + str(mask))
            logger.debug("len(angles[:,0]) %d" % len(angles[:,0]))
            for ind in imageList:
#             for ind in xrange(len(angles[:,0])):
                logger.debug("scan %d, ind: %d " % (scannr, ind ))
#                 if imageToBeUsed[scannr][ind] and mask[ind]:
#                     imageName = imageNameTemplate % (ind+1)
#                     logger.debug("processing image file " + imageName)
#                     image = np.empty((self.detectorDimensions[0],
#                                       self.detectorDimensions[1]),
#                                      np.uint32)
#                     with open(imageName) as f:
#                         image.data[:] = f.read()
#                     img2 = xu.blockAverage2D(image,
#                                              self.getNumPixelsToAverage()[0],
#                                              self.getNumPixelsToAverage()[1],
#                                              roi=self.getDetectorROI())
#                     if not arrayInitializedForScan:
#                         imagesToProcess = [imageToBeUsed[scannr][i] and mask[i] \
#                                 for i in range(len(imageToBeUsed[scannr]))]
#                         logger.debug("imagesToProcess %s " % str(imagesToProcess))
#                         if not intensity.shape[0]:
#                             # For first scan
#                             intensity = np.zeros( \
#                                 (np.count_nonzero(imagesToProcess),) + \
#                                 img2.shape)
#                             arrayInitializedForScan = True
#                         else:
#                             # Need to expand for addditional scans  
#                             offset = intensity.shape[0]
#                             intensity = np.concatenate( \
#                                 (intensity, \
#                                 (np.zeros((np.count_nonzero(imagesToProcess),) + img2.shape))), \
#                                 axis=0)
#                             arrayInitializedForScan = True
#                     intensity[foundIndex+offset,:,:] = img2
#                     for i in xrange(len(angleNames)):
#                         logger.debug("appending angles to angle2 " + 
#                                      str(scanAngle1[i][ind]))
#                         scanAngle2[i].append(scanAngle1[i][ind])
#                     foundIndex += 1
#             if len (scanAngle2[0]) > 0:
#                 for i in xrange(len(angleNames)):
#                     scanAngle[i] = \
#                         np.concatenate((scanAngle[i], \
#                                         np.array(scanAngle2[i])), \
#                                        axis=0)
#         angleList = []
# 
#         for i in range(len(angleNames)):
#             angleList.append(scanAngle[i])
#         logger.debug("Before hxrd.Ang2Q.area %s" %str(angleList))
#         if self.ubMatrix[scans[0]] is None:
#             qx, qy, qz = hxrd.Ang2Q.area(*angleList,  \
#                             roi=self.detectorROI, 
#                             Nav=self.numPixelsToAverage)
#         else:
#             qx, qy, qz = hxrd.Ang2Q.area(*angleList, \
#                             roi=self.detectorROI, 
#                             Nav=self.numPixelsToAverage, \
#                             UB = self.ubMatrix[scans[0]])
#         logger.debug("After hxrd.Ang2Q.area")
#                 
#         # apply selected transform
#         qxTrans, qyTrans, qzTrans = \
#             self.transform.do3DTransform(qx, qy, qz)
            
        qxAll = np.array([])
        qyAll = np.array([])
        qzAll = np.array([])
        intensitiesAll = np.array([])
        for procRank in xrange(workerCount):
            dataSize = None
            dataSize = comm_work.recv(dataSize, source = procRank)
            numberOfImages = dataSize['size']
            qx = np.empty((numberOfImages,))
            qy = np.empty((numberOfImages,))
            qz = np.empty((numberOfImages,))
            intensities = np.empty((numberOfImages,self.detectorROI[0], self.detectorROI[2]))
            qx = comm_work.Recv(qx, source=procRank)
            logger.debug("Master received qx %s" % qx)
            qy = comm_work.Recv(qy, source=procRank)
            logger.debug("Master received qy %s" % qy)
            qz = comm_work.Recv(qz, source=procRank)
            logger.debug("Master received qz %s" % qz)
            intensities = comm_work.Recv(intensities, source=procRank)
            qxAll = np.concatenate(qxAll, qx)
            qyAll = np.concatenate(qyAll, qy)
            qzAll = np.concatenate(qzAll, qz)
            intensitiesAll = np.concatenate(intensitiesAll, intensities, axis=0)
        comm_work.Barrier() 
        logger.debug(METHOD_EXIT_STR)
        return qxAll, qyAll, qzAll, intensitiesAll
                           
    
    def setCurrentDetector(self, currentDetector):
        self.currentDetector = currentDetector
        

    
class S1ParameterFile():
    
    
    def __init__(self, fileName):
        self.lines = []
        logger.debug(METHOD_ENTER_STR)
        import csv
        
        with open(fileName, 'r') as parFile:
            reader = csv.DictReader(parFile, delimiter=' ', 
                                skipinitialspace=True)
            numElements = 0
            self.parKeys = reader.fieldnames
            logger.debug("reader.fieldnames: " + str(self.parKeys))
            for param in EXPECTED_COLUMNS:
                if param in self.parKeys:
                    #check if other needed keys are present
                    pass
                else:
                    raise RSMap3DException("S1ParameterFile: " +
                                           str(parFile) +
                                           " does not contain the expected first " +
                                           "column " + str(param))
            #logger.debug(reader.keys())
            for row in reader:
                logger.debug("row.keys(): " + str(row.keys()))
                logger.debug("row: " + str(row[FIRST_COL]))
                if ( (not len(row[FIRST_COL])==0) and 
                     (not row[FIRST_COL].startswith("#")) and
                     (not row[FIRST_COL] == '')):
                    if len(self.lines)==0:
                        numElements = len(row)
                    else:
                        if len(row) != numElements:
                            raise RSMap3DException("S1Parameter File Line 1 has " + \
                                                   str(numElements) +  \
                                                   " elements line " + \
                                                   str(len(self.lines) + 1) + \
                                                   " has " + str(len(row)) + \
                                                   " elements.")
                    self.lines.append(row)
            
        logger.debug(METHOD_EXIT_STR)
        
    
    def getNumOfLines(self):
        return len(self.lines)
    
    def getLine(self, lineNum):
        return self.lines[lineNum-1]
    
    def getAngleData(self, lineNums):
        scanAngleData = {}
        logger.debug("Process lines: " + str(lineNums))
        logger.debug("Lines:\n" + str(self.lines))
        for lineNum in lineNums:
            logger.debug("Processing line: " + str(lineNum))
            angleData = {}
            
            angleData[S1_MOTOR] = self.lines[lineNum-1][S1_MOTOR]
            angleData[S1_START_POS] = float(self.lines[lineNum-1][S1_START_POS])
            if S1_END_POS in self.parKeys:
                angleData[S1_END_POS] = float(self.lines[lineNum-1][S1_END_POS])
            else:
                angleData[S1_END_POS] = float(self.lines[lineNum-1][S1_START_POS])

            angleData[S2_MOTOR] = self.lines[lineNum-1][S2_MOTOR]
            angleData[S2_START_POS] = float(self.lines[lineNum-1][S2_START_POS])
            if S2_END_POS in self.parKeys:
                angleData[S2_END_POS] = float(self.lines[lineNum-1][S2_END_POS])
            else:
                angleData[S2_END_POS] = float(self.lines[lineNum-1][S2_START_POS])

            angleData[D1_MOTOR] = self.lines[lineNum-1][D1_MOTOR]
            angleData[D1_START_POS] = float(self.lines[lineNum-1][D1_START_POS])
            if D1_END_POS in self.parKeys:
                angleData[D1_END_POS] = float(self.lines[lineNum-1][D1_END_POS])
            else:
                angleData[D1_END_POS] = float(self.lines[lineNum-1][D1_START_POS])

            angleData[NFRAMES] = int(self.lines[lineNum-1][NFRAMES])
            scanAngleData[lineNum] = angleData
        return scanAngleData
    
    def getFileData(self, lineNums):
        scanFileData = {}
        fileData = {}
        for lineNum in lineNums:
            fileData[IMAGE_PREFIX] = (self.lines[lineNum-1][IMAGE_PREFIX])
            fileData[IMAGE_NUMBER] = (self.lines[lineNum-1][IMAGE_NUMBER])
            fileData[FILE_EXT] = (self.lines[lineNum-1][FILE_EXT])
            scanFileData[lineNum] = fileData
        return scanFileData
    
    def getEnergy(self, lineNums):
        
        scanEnergyData = {}
        energyData = {}
        energyData[INCIDENT_ENERGY] = []
        for lineNum in lineNums:
            logger.debug("self.lines[%d][INCIDENT_ENERGY] = " % lineNum + str(self.lines[lineNum][INCIDENT_ENERGY]))
            energyData[INCIDENT_ENERGY] = \
                float(self.lines[lineNum-1][INCIDENT_ENERGY])
            scanEnergyData[lineNum] = energyData
        return scanEnergyData