'''
 Copyright (c) 2017 UChicago Argonne, LLC
 See LICENSE file.
'''
import numpy as np
from mpi4py import MPI 
import logging
import logging.config
from rsMap3D.config.rsmap3dlogging import LOGGER_NAME, LOGGER_DEFAULT
from ConfigParser import NoSectionError
import os
import sys
import xrayutilities as xu

userDir = os.path.expanduser("~")
logConfigFile = os.path.join(userDir, LOGGER_NAME + 'Log.config')
try:
    logging.config.fileConfig(logConfigFile)
except NoSectionError:
    logging.config.dictConfig(LOGGER_DEFAULT)
logger = logging.getLogger(LOGGER_NAME + ".datasource.s1mpiclient")

class s1MPIClient():

    def doInitArea(self, comm, hxrd):
        #-----Grab data for init_area
        initAreaArgs=None
        initAreaArgs = comm.bcast(initAreaArgs, root=0)
#         comm.Barrier()
        hxrd.Ang2Q.init_area(initAreaArgs['pixDir1'],
                             initAreaArgs['pixDir2'],
                             cch1=initAreaArgs['cch'][0],
                             cch2=initAreaArgs['cch'][1],
                             Nch1=initAreaArgs['detDims'][0],
                             Nch2=initAreaArgs['detDims'][1],
                             pwidth1=initAreaArgs['pixWidth'][0],
                             pwidth2=initAreaArgs['pixWidth'][1],
                             distance = initAreaArgs['distance'],
                             Nav=initAreaArgs['Nav'],
                             roi=initAreaArgs['roi'])
        
        comm.Barrier()
        return initAreaArgs
        
    def findImageQs(self):
        #initialize the communicator for this process
        comm = MPI.Comm.Get_parent()
        
        rank = comm.Get_rank()
        size = comm.Get_size()
        processorHost = MPI.Get_processor_name()
        logger.debug("Rank %d Starting findImageQs client on host %s" % 
                     (rank, processorHost))
        
        qconv = self.getQConversion(comm)
                
        hxrd = self.getHXRD(comm, qconv)
        
        initAreaArgs = self.doInitArea(comm, hxrd)

        roi = initAreaArgs['roi']
        nav = initAreaArgs['Nav']

        imageInfo = self.getImageInfo(comm)

        imageSize = imageInfo['imageSize']
        numImages = imageInfo['numImages']
        bytesPerPixel = imageInfo['bytesPerPixel']
        maxImageMem = imageInfo['maxImageMem']
        ub = imageInfo['ub']
        transform = imageInfo['transform']
        if imageSize*bytesPerPixel*numImages <= maxImageMem:
            pass
        else:
            nPasses = imageSize*bytesPerPixel*numImages/ maxImageMem + 1
            for thisPass in range(nPasses):
                xmin = []
                xmax = []
                ymin = []
                ymax = []
                zmin = []
                zmax = []
                # Get ready to calculate the qs for the areas
                area_args = {}
                area_args = comm.bcast(area_args, root=0)
#                 logger.debug("Client Rank %d area_args %s" % 
#                              (rank, str(area_args)))
                dividedImages = area_args['dividedImages']
                angles = area_args['angles']
                logger.debug("Client Rank %d dividedImages %s" % 
                             (rank, str(dividedImages)))
                logger.debug("Angles for rank %d:  %s " % (rank, list(angles[i] for i in dividedImages[rank])))
                comm.Barrier()
                angleList = []
                if len(dividedImages[rank-1]) > 0:
                    for i in range(len(angles[0])):
                            if len(dividedImages[rank]) > 1:
                                minIndex = dividedImages[rank][0]
                                maxIndex = dividedImages[rank][-1]
                                angleList.append(angles[minIndex:maxIndex+1, i])
                            else:
                                index = dividedImages[rank][0]
                                angleList.append([angles[index,i],])
                    if ub is None:
                        qx, qy, qz = hxrd.Ang2Q.area(*angleList, \
                                                     roi=roi, \
                                                     Nav=nav)
                    else:
                        qx, qy, qz = hxrd.Ang2Q.area(*angleList , \
                                                     roi=roi, \
                                                     Nav=nav, \
                                                     UB = ub)
                    qxTrans, qyTrans, qzTrans = transform.do3DTransform(qx,qy,qz)
                    idx = range(len(qxTrans))
                    # Using Maps
                
                    xmin.extend(map(np.min, qxTrans))
                    xmax.extend(map(np.max, qxTrans))
                    ymin.extend(map(np.min, qyTrans))
                    ymax.extend(map(np.max, qyTrans))
                    zmin.extend(map(np.min, qzTrans))
                    zmax.extend(map(np.max, qzTrans))
                logger.debug("Client rank %d xmin %s" % (rank, xmin))
                logger.debug("Client rank %d xmax %s" % (rank, xmax))
                logger.debug("Client rank %d ymin %s" % (rank, ymin))
                logger.debug("Client rank %d ymax %s" % (rank, ymax))
                logger.debug("Client rank %d zmin %s" % (rank, zmin))
                logger.debug("Client rank %d zmax %s" % (rank, zmax))
                logger.debug("Client rank %d Creating minMaxArray" % rank)    
                minMaxArray =np.array([np.array(xmin), \
                            np.array(xmax), \
                            np.array(ymin), \
                            np.array(ymax), \
                            np.array(zmin), 
                            np.array(zmax)])
                logger.debug("Client Rank %d minMaxArray.shape %s" % (rank, minMaxArray.shape))
                comm.Send(np.array(minMaxArray.shape), dest=0 )           
                logger.debug("Client rank %d minMaxArray %s" % (rank, str(minMaxArray)))
                comm.Send(minMaxArray, dest=0)
                comm.Barrier()
        logger.debug("Ending findImageQs client rank % on node %s" % 
                     (rank, processorHost))
        comm.Disconnect()
        
    def getImageInfo(self, comm):
        #---- Grab Image data Size, bytes/pixel
        imageInfo = None
        rank = comm.Get_rank()
        imageInfo = comm.bcast(imageInfo, root = 0)
        logger.debug("client rank %d imageInfo %s" % (rank, str(imageInfo)) )
        comm.Barrier()
        return imageInfo
    
    def getHXRD(self, comm, qconv):
        #Grab the data that will be needed for HXRD
        HXRD_args = None
        HXRD_args = comm.bcast(HXRD_args, root =0)
#       comm.Barrier()
        hxrd = xu.HXRD(HXRD_args['inplaneRef'], 
                       HXRD_args['sampleNorm'], 
                       en=HXRD_args['en'], 
                       qconv=qconv)
        comm.Barrier()
        return hxrd
    
    def getQConversion(self, comm):
        '''
        Grab the data that will be needed for xrayutilities QConversion.
        This data will be broadcast via MPI to all clients
        '''
        rank = comm.Get_rank()
        directions = None
        directions = comm.bcast(directions, root = 0)
#        comm.Barrier()
        logger.debug("Rank  %d, sampleCircleDirections: %s" % \
                     (rank , str(directions['sampleCircleDirections'])))
        logger.debug("Rank  %d, detectorCircleDirections: %s" % \
                     (rank, str(directions['detectorCircleDirections'])))
        logger.debug("Rank  %d, primaryBeamDirection: %s" % \
                 (rank, str(directions['primaryBeamDirection'])))
        qconv = xu.experiment.QConversion(directions['sampleCircleDirections'], 
                                          directions['detectorCircleDirections'], 
                                          directions['primaryBeamDirection'])
        comm.Barrier()
        return qconv
    
    def rawmap(self):
        #initialize the communicator for this process
        comm = MPI.Comm.Get_parent()
        
        rank = comm.Get_rank()
        size = comm.Get_size()
        processorHost = MPI.Get_processor_name()
        logger.debug("Rank %d Starting rawmap client on host %s, world size %d" % 
                     (rank, processorHost, size))
        intensity = np.array([])
        
        qconv = self.getQConversion(comm)

#         scanInfo = None
#         scanInfo = comm.bcast(scanInfo, root=0)
#         comm.Barrier()
                
        imageToBeUsed = None
        scans = None
        angleNames = None
        scans = comm.bcast(scans, root=0)
        comm.Barrier()
        logger.debug("Client rank %d scans: %s" % (rank, str(scans)))
        angleNames = comm.bcast(angleNames, root=0)
        comm.Barrier()
        logger.debug("Client rank %d angleNames: %s" % (rank, str(angleNames)))
        imageToBeUsed = comm.bcast(imageToBeUsed, root=0)
        comm.Barrier()
        logger.debug("Client rank %d imageToBeUsed: %s" % (rank, str(imageToBeUsed)))
        offset = 0
        scanAngle = {}
        roi = []
        numPixelsToAverage = []
        for i in xrange(len(angleNames)):
            scanAngle[i] = np.array([])
            
        for scannr in scans:
            haltMap = False
            haltMap = comm.bcast(haltMap, root=0)
            comm.Barrier()
            if haltMap:
                comm.Disconnect()
                return
            hxrd = self.getHXRD(comm, qconv)
            
            initAreaArgs = self.doInitArea(comm, hxrd)
            
            roi = initAreaArgs['roi']
            nav = initAreaArgs['Nav']
            
            imageInfo = self.getImageInfo(comm)
            
            imageSize = imageInfo['imageSize']
            numImages = imageInfo['numImages']
            bytesPerPixel = imageInfo['bytesPerPixel']
            maxImageMem = imageInfo['maxImageMem']
            ub = imageInfo['ub']
            transform = imageInfo['transform']
#             anglesShape = np.empty(2)
#             anglesShape = comm.bcast(anglesShape, root=0)

            dividedImages = None
            dividedImages = comm.bcast(dividedImages, root=0)
            logger.debug("dividedImages recvd by rank %d : %s" % (rank, dividedImages))
            comm.Barrier()
            dividedList = dividedImages['dividedList']
            angles = dividedImages['angles']
            scanAngle1 = {}
            scanAngle2 = {}
            
            firstImageForRank = dividedList[rank][0]
            lastImageForRank = dividedList[rank][-1]
            for i in xrange(len(angleNames)):
                scanAngle1[i] = \
                    angles[firstImageForRank:(lastImageForRank+1), i]
                scanAngle2[i] = []
                
            foundIndex = 0
            arrayInitializedForScan = False
            imageFileInfo = None
            imageFileInfo = comm.bcast(imageFileInfo, root=0)
            comm.Barrier()
            logger.debug("client rank %d imageFileInfo %s" % 
                         (rank, imageFileInfo))
            imageNameTemplate = imageFileInfo['imageNameTemplate']
            mask = imageFileInfo['mask']
#            imageToBeUsed = imageFileInfo['imageToBeUsed']
            detectorDims = initAreaArgs['detDims']
            numPixelsToAverage = initAreaArgs['Nav']
            roi = initAreaArgs['roi']
            logger.debug("Looping over images %d:%d" % \
                         (firstImageForRank, lastImageForRank))
            for ind in xrange(firstImageForRank, lastImageForRank+1):
                logger.debug("Client rank %d, scan %d, ind: %d" % 
                             (rank, scannr, ind))
                if imageToBeUsed[scannr][ind] and mask[ind]:
                    imageName = imageNameTemplate % (ind + 1)
                    image = np.empty((detectorDims[0], detectorDims[1]), np.uint32)
                    with open(imageName) as f:
                        image.data[:] = f.read()
                    img2 = xu.blockAverage2D(image,
                                             numPixelsToAverage[0],
                                             numPixelsToAverage[1],
                                             roi=roi)
                    if not arrayInitializedForScan:
#                         imagesToProcess = [imageToBeUsed[scannr][i] and mask[i] \
#                                            for i in range(len(imageToBeUsed[scannr]))]
                        imagesToProcess = [imageToBeUsed[scannr][i] and mask[i] \
                                           for i in dividedList[rank]]                        
                        logger.debug("imagesToProcess %s" % str(imagesToProcess))
                        if not intensity.shape[0]:
                            # For the first scan
                            intensity = np.zeros((np.count_nonzero(imagesToProcess),) + \
                                img2.shape)
                            arrayInitializedForScan = True
                        else:
                            # Need to expand for additional scans
                            offset = intensity.shape[0]
                            intensity = np.concatenate( \
                                (intensity, \
                                (np.zeros((np.count_nonzero(imagesToProcess),) + img2.shape))), \
                                                       axis = 0)
                            arrayInitializedForScan = True
                    intensity[foundIndex+offset, :,:] = img2
                    for i in xrange(len(angleNames)):
                        logger.debug("rawmap client rank %d, appending angles to angle2 %s" % (rank, scanAngle1[i][ind-firstImageForRank]))
                        scanAngle2[i].append(scanAngle1[i][ind-firstImageForRank])
                    foundIndex += 1
            if len(scanAngle2[0]) > 0:
                for i in xrange(len(angleNames)):
                    scanAngle[i] = \
                        np.concatenate((scanAngle[i], \
                                        np.array(scanAngle2[i])) ,
                                       axis = 0)           
        angleList = []
        for i in range(len(angleNames)):
            angleList.append(scanAngle[i])

        logger.debug ("rawmap client rank %d roi before hxrd.Ang2q.area %s" % \
                      (rank, roi))
        logger.debug ("rawmap client rank %d numPixelsToAverage before hxrd.Ang2q.area %s" % \
                      (rank, numPixelsToAverage))
        logger.debug ("rawmap client rank %d angleList before hxrd.Ang2q.area %s %s %s" % \
                      (rank, angleList[0], angleList[1], angleList[2]))
        if ub ==None:
            qx, qy, qz = hxrd.Ang2Q.area(*angleList,
                                         roi=roi,
                                         Nav = numPixelsToAverage)
        else:
            qx, qy, qz = hxrd.Ang2Q.area(*angleList,
                                         roi=roi,
                                         Nav = numPixelsToAverage,
                                         UB = ub)
        logger.debug("After hxrd")
        
        #Apply transform
        qxTrans, qyTrans, qzTrans = \
            transform.do3DTransform( qx, qy, qz)
        qx = np.ascontiguousarray(qxTrans)
        dataSize = {"size" : qxTrans.shape[0]}
        comm.send(dataSize, dest = 0)
        logger.debug("client rank %d qxTrans %s flags %s dtype %s type %s qx[0] type %s" % (rank, str(qx), qx.flags, qx.dtype, type(qx), type(qx[0])))
        comm.Send(qx, dest=0)
        comm.Send(qyTrans, dest=0)
        comm.Send(qzTrans, dest=0)
        comm.Send(intensity, dest=0)
        comm.Barrier()
        logger.debug("Ending findImageQs client rank % on node %d")
        comm.Disconnect()

if __name__ == "__main__":
    args = sys.argv
    print sys.argv
    client = s1MPIClient()
    if sys.argv[1] == "findImageQs":
        client.findImageQs()
    elif sys.argv[1] == 'rawmap':
        client.rawmap()