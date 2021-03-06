from CalibrationDataProvider import AbstractCalibrationDataProvider
import glob
import os

class CalibrationDataProvider(AbstractCalibrationDataProvider):

    def __init__(self, dataSource="", verbose=False):
        super(CalibrationDataProvider, self).__init__()

        self.dataPath = dataSource
        self.dacTable = {
            'vdig': 'Vdd',
            'vana': 'Vana',
            'vsh': 'Vsh',
            'vcomp': 'Vcomp',
            'vwllpr': 'VwllPr',
            'vwllsh': 'VwllSh',
            'vhlddel': 'VHldDel',
            'vtrim': 'Vtrim',
            'vthrcomp': 'VcThr',
            'vibias_bus': 'VIbias_bus',
            'phoffset': 'PHOffset',
            'vcomp_adc': 'Vcomp_ADC',
            'phscale': 'PHScale',
            'vicolor': 'VIColOr',
            'vcal': 'Vcal',
            'caldel': 'CalDel',
            'ctrlreg': 'ChipContReg',
            'wbc': 'WBC',
            'readback': 'Readback',
        }

    def getLocalModuleDataPath(self, ModuleID, options = {}):

        pathParts = self.dataPath.split('/')
        pathParts.append("%s_FullQualification_*"%ModuleID)
        pathParts.append("*_%s"%(options['Test'] if 'Test' in options else 'm20'))

        if len(pathParts[0]) == 0 or pathParts[0][-1] == ":":
            pathParts[0] = pathParts[0] + '/'

        globPath = os.path.join(*pathParts)
        folders = glob.glob(globPath)
        folders.sort()

        # add Xray qualifications
        pathParts = self.dataPath.split('/')
        pathParts.append("%s_Xray*_*"%ModuleID)
        pathParts.append("*_%s"%options['tempnominal'])
        if len(pathParts[0]) == 0 or pathParts[0][-1] == ":":
            pathParts[0] = pathParts[0] + '/'
        globPath = os.path.join(*pathParts)
        foldersXray = glob.glob(globPath)
        if len(foldersXray) > 0:
            foldersXray.sort()
            folders += foldersXray


        return folders


    def getRocDacs(self, ModuleID, options = {}):
        dacs = []

        localModuleDataPaths = self.getLocalModuleDataPath(ModuleID=ModuleID, options=options)

        dacsFound = False
        for localModuleDataPath in localModuleDataPaths:
            for iROC in range(self.nROCs):
                dacFileName = os.path.join(localModuleDataPath, "dacParameters%s_C%d.dat"%(options['TrimValue'] if 'TrimValue' in options else '', iROC))
                rocDACs = []
                if os.path.isfile(dacFileName):
                    with open(dacFileName, 'r') as dacFile:
                        for line in dacFile:
                            dacLine = [x.lower() for x in line.strip().split(' ') if len(x) > 0]
                            if dacLine[1] in self.dacTable:
                                rocDACs.append({'Name': self.dacTable[dacLine[1]], 'Value': dacLine[2]})
                    dacsFound = True
                    dacs.append({'ROC': iROC, 'DACs': rocDACs})
            if dacsFound:
                if len(localModuleDataPaths) > 1:
                    print "more than one folder found, using this one:"
                    print "  ->", localModuleDataPath
                break


        return dacs


    def getTrimBits(self, ModuleID, options = {}):

        trims = []
        localModuleDataPaths = self.getLocalModuleDataPath(ModuleID=ModuleID, options=options)

        trimsFound = False
        for localModuleDataPath in localModuleDataPaths:
            for iROC in range(self.nROCs):
                trimFileName = os.path.join(localModuleDataPath, "trimParameters%s_C%d.dat" %(options['TrimValue'] if 'TrimValue' in options else '', iROC))
                rocTrims = [self.defaultTrim]*self.nPix
                if os.path.isfile(trimFileName):
                    trimsFound = True
                    with open(trimFileName, 'r') as trimFile:
                        for line in trimFile:
                            trimLine = [x.lower() for x in line.strip().split(' ') if len(x) > 0]
                            if trimLine[1].lower() == 'pix':
                                iPix = int(trimLine[2]) * self.nRows + int(trimLine[3])
                                rocTrims[iPix] = int(trimLine[0])
                            else:
                                raise NameError('invalid trim bits file format!')
                    trims.append({'ROC': iROC, 'Trims': rocTrims})
            if trimsFound:
                if len(localModuleDataPaths) > 1:
                    print "more than one folder found, using this one:"
                    print "  ->", localModuleDataPath
                break

        return trims

    def getTbmParameters(self, ModuleID, options={}):
        raise NotImplementedError('getTbmParameters() not implemented!')