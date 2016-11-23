from CalibrationDataProvider import AbstractCalibrationDataProvider
import os

class CalibrationDataProvider(AbstractCalibrationDataProvider):

    def __init__(self, dataSource = None):
        super(CalibrationDataProvider, self).__init__()

    # initialize DACs with default value
    def getRocDacs(self, ModuleID, options = {}):
        dacs = []
        for roc in range(self.nROCs):
            rocDACs = [
                {'Name': 'Vdd', 'Value': '6'},
                {'Name': 'Vana', 'Value': '81'},
                {'Name': 'Vsh', 'Value': '30'},
                {'Name': 'Vcomp', 'Value': '12'},
                {'Name': 'VwllPr', 'Value': '150'},
                {'Name': 'VwllSh', 'Value': '150'},
                {'Name': 'VHldDel', 'Value': '250'},
                {'Name': 'Vtrim', 'Value': '0'},
                {'Name': 'VcThr', 'Value': '85'},
                {'Name': 'VIbias_bus', 'Value': '30'},
                {'Name': 'PHOffset', 'Value': '185'},
                {'Name': 'Vcomp_ADC', 'Value': '50'},
                {'Name': 'PHScale', 'Value': '65'},
                {'Name': 'VIColOr', 'Value': '100'},
                {'Name': 'Vcal', 'Value': '200'},
                {'Name': 'CalDel', 'Value': '133'},
                {'Name': 'TempRange', 'Value': '0'},
                {'Name': 'WBC', 'Value': '100'},
                {'Name': 'ChipContReg', 'Value': '0'},
                {'Name': 'Readback', 'Value': '0'},
            ]
            dacs.append({'ROC': roc, 'DACs': rocDACs})
        print "  -> created list of default DACs for %d ROCs"%self.nROCs
        return dacs

    # default trimbit configuration
    def getTrimBits(self, ModuleID, options={}):
        trims = []
        for iRoc in range(self.nROCs):
            rocTrims = [self.defaultTrim] * self.nPix
            trims.append({'ROC': iRoc, 'Trims': rocTrims})
        print "  -> created list of default trimbits(=%d) for %d ROCs"%(self.defaultTrim, self.nROCs)
        return trims

    # default TBM settings
    def getTbmParameters(self, ModuleID, options={}):
        tbmParameters = [
            {'Name': 'TBMABase0', 'Value': 0},
            {'Name': 'TBMBBase0', 'Value': 0},
            {'Name': 'TBMAAutoReset', 'Value': 0},
            {'Name': 'TBMBAutoReset', 'Value': 0},
            {'Name': 'TBMANoTokenPass', 'Value': 0},
            {'Name': 'TBMBNoTokenPass', 'Value': 0},
            {'Name': 'TBMADisablePKAMCounter', 'Value': 1},
            {'Name': 'TBMBDisablePKAMCounter', 'Value': 1},
            {'Name': 'TBMAPKAMCount', 'Value': 5},
            {'Name': 'TBMBPKAMCount', 'Value': 5},
            {'Name': 'TBMPLLDelay', 'Value': 52},
            {'Name': 'TBMADelay', 'Value': 100},
            {'Name': 'TBMBDelay', 'Value': 100},
        ]
        return tbmParameters

    # default mask bits, 0=unmasked, 1=masked
    def getMaskBits(self, ModuleID, options={}):
        masks = []
        for iRoc in range(self.nROCs):
            rocMasks = [self.defaultMask] * self.nPix
            masks.append({'ROC': iRoc, 'Masks': rocMasks})
        print "  -> created list of default maskbits(=%d) for %d ROCs"%(self.defaultMask, self.nROCs)
        return masks


    # default readback calibration
    #  mean values from 4272 ROCs from L2 module qualification, 23.11.2016
    def getTbmParameters(self, ModuleID, options={}):
        readbackParameters = [
            {'Name': 'par0vd', 'Value': -3.009},       # rms = 5.55
            {'Name': 'par1vd', 'Value': 64.55},        # rms = 3.33
            {'Name': 'par0va', 'Value': -1.72},        # rms = 3.67
            {'Name': 'par1va', 'Value': 64.15},        # rms = 4.98
            {'Name': 'par0rbia', 'Value': 11.49},      # rms = 2.69
            {'Name': 'par1rbia', 'Value': 1.072},      # rms = 0.03
            {'Name': 'par0tbia', 'Value': 4.466},      # rms = 0.44
            {'Name': 'par1tbia', 'Value': 0.2543},     # rms = 0.02
            {'Name': 'par2tbia', 'Value': -2.036e-4},  # rms = 4.4e-5
            {'Name': 'par0ia', 'Value': -4.597},       # rms = 3.17
            {'Name': 'par1ia', 'Value': 3.725},        # rms = 0.55
            {'Name': 'par2ia', 'Value': 0.0247},       # rms = 0.0007
        ]
        return readbackParameters