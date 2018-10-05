from monocle import MonocleWrapper
from rm import RmWrapper
import logging

log = logging.getLogger(__name__)


class DbWrapper:
    def __init__(self, method, host, port, user, password, database, timezone, uniqueHash = "123"):
        self.__method = method
        if self.__method == "rm":
            self.__dbWrapperUsed = RmWrapper(host, port, user, password, database, timezone, uniqueHash)
        else:
            self.__dbWrapperUsed = MonocleWrapper(host, port, user, password, database, timezone, uniqueHash)

    def ensureLastUpdatedColumn(self):
        if self.__method == "rm":
            log.debug("No need to check for last_updated in RM")
            return True
        else:
            return self.__dbWrapperUsed.ensureLastUpdatedColumn()

    def autoHatchEggs(self):
        return self.__dbWrapperUsed.auto_hatch_eggs()

    def dbTimeStringToUnixTimestamp(self, timestring):
        return self.__dbWrapperUsed.dbTimeStringToUnixTimestamp(timestring)

    def getNextRaidHatches(self, delayAfterHatch):
        return self.__dbWrapperUsed.getNextRaidHatches(delayAfterHatch)

    def createHashDatabaseIfNotExists(self):
        return self.__dbWrapperUsed.createHashDatabaseIfNotExists()

    def checkForHash(self, imghash, type, raidNo, distance=4):
        return self.__dbWrapperUsed.checkForHash(imghash, type, raidNo, distance)
        
    def getAllHash(self, type):
        return self.__dbWrapperUsed.getAllHash(type)

    def insertHash(self, imghash, type, id, raidNo):
        return self.__dbWrapperUsed.insertHash(imghash, type, id, raidNo)

    def deleteHashTable(self, ids, type, mode=' not in ', field = ' id '):
        return self.__dbWrapperUsed.deleteHashTable(ids, type, mode, field)

    def submitRaid(self, gym, pkm, lvl, start, end, type, raidNo, captureTime, MonWithNoEgg=False):
        return self.__dbWrapperUsed.submitRaid(gym, pkm, lvl, start, end, type, raidNo, captureTime, MonWithNoEgg)

    def readRaidEndtime(self, gym, raidNo):
        return self.__dbWrapperUsed.readRaidEndtime(gym, raidNo)

    def getRaidEndtime(self, gym, raidNo):
        return self.__dbWrapperUsed.getRaidEndtime(gym, raidNo)

    def raidExist(self, gym, type, raidNo, mon = 0):
        return self.__dbWrapperUsed.raidExist(gym, type, raidNo, mon)

    def refreshTimes(self, gym, raidNo, captureTime):
        return self.__dbWrapperUsed.refreshTimes(gym, raidNo, captureTime)

    def getNearGyms(self, lat, lng, hash, raidNo, dist):
        return self.__dbWrapperUsed.getNearGyms(lat, lng, hash, raidNo, dist)
        
    def checkGymsNearby(self, lat, lng, hash, raidNo, gymId):
        return self.__dbWrapperUsed.checkGymsNearby(lat, lng, hash, raidNo, gymId)
        
    def updateInsertWeather(self, lat, lng, weatherid, captureTime):
        return self.__dbWrapperUsed.updateInsertWeather(lat, lng, weatherid, captureTime)

    def setScannedLocation(self, lat, lng, captureTime):
        return self.__dbWrapperUsed.setScannedLocation(lat, lng, captureTime)

    def downloadDbCoords(self):
        return self.__dbWrapperUsed.downloadDbCoords()

    def downloadGymImages(self):
        return self.__dbWrapperUsed.downloadGymImages()
        
    def clearHashGyms(self, mons):
        return self.__dbWrapperUsed.clearHashGyms(mons)
