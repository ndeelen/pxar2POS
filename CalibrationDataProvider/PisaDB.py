from CalibrationDataProvider import AbstractCalibrationDataProvider

import MySQLdb
import getpass
import urllib
import os
import json
try:
    import ROOT
except:
    pass

class CalibrationDataProvider(AbstractCalibrationDataProvider):

    def __init__(self, dataSource = None):
        # module/chip properties
        self.nROCs = 16
        self.nRows = 80
        self.nCols = 52
        self.nPix = self.nRows * self.nCols

        # default trim bit value. 0=lowest threshold, 15=highest threshold
        self.defaultTrim = 15

        # database url
        self.dataPath = dataSource
        self.dbServer = dataSource
        self.dbUrl = 'http://' + self.dbServer

        self.queryStringFulltests = '''
SELECT * FROM inventory_fullmodule
  JOIN test_fullmodulesummary ON test_fullmodulesummary.TEST_ID = LASTTEST_FULLMODULE
  JOIN test_fullmodule ON test_fullmodule.SUMMARY_ID = LASTTEST_FULLMODULE
  JOIN test_fullmoduleanalysis ON test_fullmoduleanalysis.TEST_ID = test_fullmodule.LASTANALYSIS_ID
WHERE inventory_fullmodule.FULLMODULE_ID = %s AND tempnominal LIKE %s LIMIT 10;
        '''

        self.queryStringFulltestDacs = '''
SELECT * FROM test_dacparameters WHERE FULLMODULEANALYSISTEST_ID = %s AND TRIM_VALUE = %s ORDER BY ROC_POS LIMIT 16;
        '''

        self.queryStringFulltestData = '''
        SELECT * FROM test_data WHERE DATA_ID = %s LIMIT 1;
        '''

        self.dacTable = {
            'VDIG': 'Vdd',
            'VANA': 'Vana',
            'VSH': 'Vsh',
            'VCOMP': 'Vcomp',
            'VWLLPR': 'VwllPr',
            'VWLLSH': 'VwllSh',
            'VHLDDEL': 'VHldDel',
            'VTRIM': 'Vtrim',
            'VTHRCOMP': 'VcThr',
            'VIBIAS_BUS': 'VIbias_bus',
            'PHOFFSET': 'PHOffset',
            'VCOMP_ADC': 'Vcomp_ADC',
            'PHSCALE': 'PHScale',
            'VICOLOR': 'VIColOr',
            'VCAL': 'Vcal',
            'CALDEL': 'CalDel',
            'CTRLREG': 'ChipContReg',
            'WBC': 'WBC',
            'READBACK': 'Readback', #this does not exist in DB!
            'TEMPRANGE': 'TempRange', #this does not exist in DB!
        }

        # connect to database
        self.dbUser = "reader"
        self.dbName = "prod_pixel"
        print "connect to {dbUser}@{dbServer} database: {dbName}".format(dbUser=self.dbUser, dbServer=self.dbServer, dbName=self.dbName)
        Password = self.getDbPassword(self.dbUser)
        self.db = MySQLdb.connect(host=self.dbServer, user=self.dbUser, passwd=Password, db=self.dbName)

        try:
            self.saveDbPassword(self.dbUser, Password)
        except:
            print "could not save DB password to local file 'db.auth'"

        # remote paths to download files
        self.remotePathTrimBitMap = '/Chips/Chip{iRoc}/TrimBitMap/TrimBitMap.root'
        self.remotePathTBM = '/TBM/KeyValueDictPairs.json'

        # temp folder for downloads from database
        try:
            os.mkdir('temp')
        except:
            pass

    def getDbPassword(self, username):
        dbPassFileName = 'db.auth'
        password = ''
        passwordFound = False
        try:
            if os.path.isfile(dbPassFileName):
                with open(dbPassFileName, 'r') as dbPassFile:
                    for line in dbPassFile:
                        if line.split(':')[0].strip() == username:
                            password = line.split(':')[1].strip() if len(line.split(':')) > 1 else ''
                            passwordFound = True
                            break
        except:
            pass

        if not passwordFound:
            password = getpass.getpass()

        return password

    def saveDbPassword(self, username, password):
        dbPassFileName = 'db.auth'
        with open(dbPassFileName, 'w') as dbPassFile:
            line = username + ':' + password
            dbPassFile.write(line)


    def getFulltestRow(self, ModuleID, tempnominal):

        cursor = self.db.cursor(cursorclass=MySQLdb.cursors.DictCursor)

        # get list of fulltests
        cursor.execute(self.queryStringFulltests, (ModuleID, tempnominal + '%'))
        self.db.commit()
        rows = cursor.fetchall()
        if len(rows) < 1:
            print "ERROR: no Fulltests found for tempnominal=", tempnominal
            return None

        if len(rows) > 1:
            print "WARNING: multiple Fulltests found for tempnominal=", tempnominal, " using the first one"

        row = rows[0] # take first one
        return row


    def getRocDacs(self, ModuleID, options = {}):

        # initialize
        dacs = []
        tempnominal = options['tempnominal'] if 'tempnominal' in options else 'm20_1'
        TrimValue =  options['TrimValue'] if 'TrimValue' in options else '-1'
        row = self.getFulltestRow(ModuleID, tempnominal)

        if row:
            fulltestAnalysisId = row['LASTANALYSIS_ID']
            try:
                print "  -> Fulltest analysis ID: ", fulltestAnalysisId
                print "  -> tempnominal: ", tempnominal, " -> ", row['tempnominal']
                print "  -> Temperature: ", row['TEMPVALUE']
                print "  -> Analysis MoReWeb version: ", row['MACRO_VERSION']
            except:
                pass

            # get DACs
            cursor = self.db.cursor(cursorclass=MySQLdb.cursors.DictCursor)
            cursor.execute(self.queryStringFulltestDacs, (fulltestAnalysisId, TrimValue))
            self.db.commit()
            rows = cursor.fetchall()
            nDACs = 0
            for row in rows:
                rocDACs = []
                for dbDACName, POSName in self.dacTable.items():
                    if dbDACName in row:
                        rocDACs.append({'Name': POSName, 'Value': '%d'%row[dbDACName]})
                        nDACs += 1

                if len([x for x in rocDACs if x['Name'] == 'TempRange']) < 1:
                    rocDACs.append({'Name': 'TempRange', 'Value': '0'})

                if len([x for x in rocDACs if x['Name'] == 'Readback']) < 1:
                    rocDACs.append({'Name': 'Readback', 'Value': '1'})

                dacs.append({'ROC': row['ROC_POS'], 'DACs': rocDACs})

            print " -> {nDACs} DACs read for {ModuleID}".format(ModuleID=ModuleID, nDACs=nDACs)
        else:
            print "ERROR: Fulltest not found"

        return dacs


    def getRemoteResultsPath(self, ModuleID, options={}):

        # initialize
        tempnominal = options['tempnominal'] if 'tempnominal' in options else 'm20_1'

        # get fulltest analysis ID and data ID
        row = self.getFulltestRow(ModuleID, tempnominal)

        if row:
            dataId = row['test_fullmoduleanalysis.DATA_ID']
            print "  -> Fulltest analysis ID: ", row['LASTANALYSIS_ID']
            print "  -> data ID: ", dataId

            # get remote data path for the data ID
            cursor = self.db.cursor(cursorclass=MySQLdb.cursors.DictCursor)
            cursor.execute(self.queryStringFulltestData, (dataId, ))
            self.db.commit()
            rows = cursor.fetchall()
            if len(rows) > 0:
                remoteModuleDataPath = self.dbUrl + rows[0]['PFNs'].replace('file:', '')
                print "  -> remote path: ", remoteModuleDataPath
                return remoteModuleDataPath
        else:
            return None


    def getTrimBits(self, ModuleID, options={}):
        trims = []

        remoteModuleDataPath = self.getRemoteResultsPath(ModuleID=ModuleID, options=options)
        if remoteModuleDataPath:
            for iRoc in range(self.nROCs):
                remoteFileName = self.remotePathTrimBitMap.format(iRoc=iRoc)
                localFileName = 'temp/TrimBitMap%sROC%d.root'%(ModuleID, iRoc)
                urllib.urlretrieve(remoteModuleDataPath + remoteFileName, localFileName)
                rocTrims = [self.defaultTrim] * self.nPix

                # read trim file
                RootFile = ROOT.TFile.Open(localFileName)
                RootFileCanvas = RootFile.Get("c1")
                PrimitivesList = RootFileCanvas.GetListOfPrimitives()
                histName = 'TrimBitMap'
                ClonedROOTObject = None
                HistogramFound = False
                for i in range(0, PrimitivesList.GetSize()):
                    if PrimitivesList.At(i).GetName().find(histName) > -1:
                        ClonedROOTObject = PrimitivesList.At(i).Clone('TH2DTrimBitMap%sROC%d'%(ModuleID, iRoc))
                        try:
                            ClonedROOTObject.SetDirectory(0)
                        except:
                            pass
                        HistogramFound = True
                        RootFile.Close()
                        break
                if HistogramFound:
                    nBinsX = ClonedROOTObject.GetXaxis().GetNbins()
                    nBinsY = ClonedROOTObject.GetYaxis().GetNbins()
                    assert nBinsX == self.nCols and nBinsY == self.nRows

                    for col in range(self.nCols):
                        for row in range(self.nRows):
                            rocTrims[col * self.nRows + row] = ClonedROOTObject.GetBinContent(1 + col, 1 + row)

                trims.append({'ROC': iRoc, 'Trims': rocTrims})
            print " -> trim parameters read for {ModuleID}".format(ModuleID=ModuleID)
        return trims


    def getTbmParameters(self, ModuleID, options={}):
        tbmParameters = []

        tbmParameters.append({'Name': 'TBMABase0', 'Value': 0})
        tbmParameters.append({'Name': 'TBMBBase0', 'Value': 0})
        tbmParameters.append({'Name': 'TBMAAutoReset', 'Value': 0})
        tbmParameters.append({'Name': 'TBMBAutoReset', 'Value': 0})
        tbmParameters.append({'Name': 'TBMANoTokenPass', 'Value': 0})
        tbmParameters.append({'Name': 'TBMBNoTokenPass', 'Value': 0})
        tbmParameters.append({'Name': 'TBMADisablePKAMCounter', 'Value': 1})
        tbmParameters.append({'Name': 'TBMBDisablePKAMCounter', 'Value': 1})
        tbmParameters.append({'Name': 'TBMAPKAMCount', 'Value': 5})
        tbmParameters.append({'Name': 'TBMBPKAMCount', 'Value': 5})

        remoteModuleDataPath = self.getRemoteResultsPath(ModuleID=ModuleID, options=options)
        if remoteModuleDataPath:
            remoteFileName = self.remotePathTBM
            localFileName = 'temp/TBM_%s.json'%(ModuleID)
            urllib.urlretrieve(remoteModuleDataPath + remoteFileName, localFileName)

            with open(localFileName) as data_file:
                data = json.load(data_file)

            try:
                tbmParameters.append({'Name': 'TBMPLLDelay', 'Value': int(data['Core0a_basee']['Value'].replace('0x', ''), 16)})
                tbmParameters.append({'Name': 'TBMADelay', 'Value': int(data['Core0a_basea']['Value'].replace('0x', ''), 16)})
                tbmParameters.append({'Name': 'TBMBDelay', 'Value': int(data['Core0b_basea']['Value'].replace('0x', ''), 16)})
            except:
                raise NameError("TBM/KeyValueDictPairs.json: can't read TBM parameters from JSON file")

            print " -> TBM parameters read for {ModuleID}".format(ModuleID=ModuleID)
        return tbmParameters
