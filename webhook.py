import logging
from walkerArgs import parseArgs
import requests
import json
import datetime
import time
import sys
reload(sys)


sys.setdefaultencoding('utf8')

log = logging.getLogger(__name__)
args = parseArgs()

class Webhook:
    def __init__(self, dbIp, dbPort, dbUser, dbPassword, dbName, timezone, hash):
        self.dbIp = dbIp
        self.dbPort = dbPort
        self.dbUser = dbUser
        self.dbPassword = dbPassword
        self.dbName = dbName
        self.timezone = timezone
        self.uniqueHash = hash

        self.dbWrapper = DbWrapper(self.dbIp, self.dbPort, self.dbUser, self.dbPassword, self.dbName, self.timezone, self.uniqueHash)
        
        
    def getEndTime(self, gym, pkm, lvl, start, end, type, raidNo, captureTime):
        print('[Crop: ' + str(raidNo) + ' (' + str(self.uniqueHash) +') ] ' + 'submitRaid: %s already submitted - ignoring' % str(type))
    