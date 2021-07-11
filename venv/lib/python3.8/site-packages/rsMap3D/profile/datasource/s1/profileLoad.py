from rsMap3D.datasource.s1highenergydiffractionds import S1HighEnergyDiffractionDS
import os
import logging.config
from rsMap3D.config.rsmap3dlogging import LOGGER_NAME
from rsMap3D.transforms.unitytransform3d import UnityTransform3D
from rsMap3D.config.rsmap3dconfigparser import RSMap3DConfigParser

def updateProgress(value, max):
    print("progress %d/%d" % (value, max))

if __name__ == "__main__":
    print "Profiling Sector1 Load Phase"
    THIS_DIR = os.path.dirname(os.path.abspath(__file__))
    configDir = os.path.join(THIS_DIR, '../../../resources/config')
    userDir = os.path.expanduser("~")
    logConfigFile = os.path.join(userDir, LOGGER_NAME + 'Log.config')
    print logConfigFile
    logging.config.fileConfig(logConfigFile)
    logger = logging.getLogger(LOGGER_NAME)
    projectDir = os.path.join(configDir, "../1-idscan")
    projectName = "fastpar_startup_oct16_FF1"
    projectExtension = ".par"
    instConfig = os.path.join(projectDir, "1-ID-E_AeroTable.xml")
    detConfig = os.path.join(projectDir, "1-ID-GE.xml")
    transform = UnityTransform3D()
    pixelsToAverage = [1,1]
    scanList = [3,]
    detRoi = [1,2048,1,2048]
    imageDirName = ""         #fake since not used here.
    appConfig = RSMap3DConfigParser()
    
    ds = S1HighEnergyDiffractionDS(str(projectDir), \
                                          str(projectName), \
                                          str(projectExtension), \
                                          str(instConfig), \
                                          str(detConfig), \
                                          imageDirName, \
                                          transform=transform,
                                          scanList=scanList,
                                          pixelsToAverage= pixelsToAverage,
                                          badPixelFile=None,
                                          flatFieldFile=None,
                                          appConfig=appConfig)
    ds.setCurrentDetector('ge3')
    ds.setProgressUpdater(updateProgress)
    ds.loadSource()
