import cv2
import numpy as np
from PIL import Image
import pytesseract
import datetime
import time
import matching as mt
import logging
from walkerArgs import parseArgs
from skimage.measure import compare_ssim as ssim
import glob, os
import mysql
import mysql.connector
import imutils
from dbWrapper import *

log = logging.getLogger(__name__)
args = parseArgs()

monegg = []
monegg.append(args.egg1_mon_id)
monegg.append(args.egg2_mon_id)
monegg.append(args.egg3_mon_id)
monegg.append(args.egg4_mon_id)
monegg.append(args.egg5_mon_id)

eggIdsByLevel = [1, 1, 2, 2, 3] #egg IDs are always the same, just remember to decrement your raidlevel

class Scanner:
    def __init__(self, dbIp, dbPort, dbUser, dbPassword, dbName, tempPath, unknownPath, timezone):
        self.dbIp = dbIp
        self.dbPort = dbPort
        self.dbUser = dbUser
        self.dbPassword = dbPassword
        self.dbName = dbName
        self.tempPath = tempPath
        self.unknownPath = unknownPath
        self.timezone = timezone

        if not os.path.exists(self.tempPath):
            log.info('Temp directory created')
            os.makedirs(self.tempPath)

        if not os.path.exists(self.unknownPath):
            log.info('Unknow directory created')
            os.makedirs(self.unknownPath)

    def submitRaid(self, guid, pkm, lvl, start, end, type):
        log.debug("Submitting raid")
        now = datetime.datetime.now()
        date1 = str(now.year) + "-0" + str(now.month) + "-" + str(now.day)
        today1 = date1 + " " + str(now.hour - (self.timezone)) + ":" + str(now.minute) + ":" + str(now.second)

        try:
            connection = mysql.connector.connect(host = self.dbIp, user = self.dbUser, passwd = self.dbPassword, db = self.dbName, port = self.dbPort)
        except:
            log.error("Error while connect to MySql Database")
            exit(0)

        cursor = connection.cursor()
        log.debug("Submitting something of type %s" % type)
        if type == 'EGG':
            #query = " UPDATE raid SET level = %s, spawn=FROM_UNIXTIME(%s), start=FROM_UNIXTIME(%s), end=FROM_UNIXTIME(%s), pokemon_id = %s, cp = %s, move_1 = %s, move_2 = %s, last_scanned = %s WHERE gym_id = %s "
            #data = (lvl, start, start, end, monegg[int(lvl) - 1], "999", "1", "1",  today1, guid)
            log.info("Submitting Egg. Gym: %s, Lv: %s, Start and Spawn: %s, End: %s, last_scanned: %s" % (guid, lvl, start, end, today1))
            query = (' INSERT INTO raid (gym_id, level, spawn, start, end, pokemon_id, cp, move_1, ' +
                'move_2, last_scanned) VALUES(%s, %s, FROM_UNIXTIME(%s), FROM_UNIXTIME(%s), ' +
                'FROM_UNIXTIME(%s), %s, %s, %s, %s, FROM_UNIXTIME(%s)) ON DUPLICATE KEY UPDATE level = %s, ' +
                'spawn=FROM_UNIXTIME(%s), start=FROM_UNIXTIME(%s), end=FROM_UNIXTIME(%s), ' +
                'pokemon_id = %s, cp = %s, move_1 = %s, move_2 = %s, last_scanned = FROM_UNIXTIME(%s)')
            data = (guid, lvl, start, start, end, None, "999", "1", "1", time.time(), #TODO: check None vs null?
                lvl, start, start, end, None, "999", "1", "1", time.time())
            #data = (lvl, start, start, end, None, "999", "1", "1", today1, guid)
            cursor.execute(query, data)
        else:
            log.info("Submitting mon. PokemonID %s, Lv %s, last_scanned %s, gymID %s" % (pkm, lvl, today1, guid))
            #query = " UPDATE raid SET level = %s, pokemon_id = %s, cp = %s, move_1 = %s, move_2 = %s, last_scanned = %s WHERE gym_id = %s "
            query = " UPDATE raid SET pokemon_id = %s, cp = %s, move_1 = %s, move_2 = %s, last_scanned = FROM_UNIXTIME(%s) WHERE gym_id = %s "
            data = (pkm, "999", "1", "1",  time.time(), guid)
            #data = (lvl, pkm, "999", "1", "1",  time.time(), guid)
            cursor.execute(query, data)

        connection.commit()
        return 0

    def detectRaidTime(self, raidpic, hash, raidNo):
        log.debug('Reading Raidtimer')
        raidtimer = raidpic[170:210, 0:297]
        raidtimer = cv2.resize(raidtimer, (0,0), fx=3, fy=3)
        emptyRaidTempPath = self.tempPath + "/" + str(raidNo) + str(hash) + "_emptyraid.png"
        cv2.imwrite(emptyRaidTempPath, raidtimer)
        rt = Image.open(emptyRaidTempPath)
        gray = rt.convert('L')
        bw = gray.point(lambda x: 0 if x<210 else 255, '1')
        raidtimer = pytesseract.image_to_string(bw, config='-psm 7').replace(' ', '').replace('~','').replace('o','0').replace('O','0').replace('-','')
        log.debug(raidtimer)
        #cleanup
        os.remove(emptyRaidTempPath)
        raidFound = len(raidtimer) > 0

        if raidFound:
            if ':' in raidtimer:
                now = datetime.datetime.now()
                log.info("getHatchTime: found raidtimer '%s'" % raidtimer)
                hatchTime = getHatchTime(self, raidtimer)
                if hatchTime:
                    log.info("getHatchTime: Hatchtime %s" % str(hatchTime))
                    #raidstart = getHatchTime(self, raidtimer) - self.timezone * (self.timezone*60*60)
                    raidstart = hatchTime - (self.timezone * 60 * 60)
                    raidend = hatchTime + 45 * 60 - (self.timezone * 60 * 60)
                    #raidend = getHatchTime(self, raidtimer) + int(45*60) - (self.timezone*60*60)
                    log.debug('Start: ' + str(raidstart) + ' End: ' + str(raidend))
                    return (raidFound, True, raidstart, raidend)
                else:
                    return (raidFound, False, None, None)

            else:
                return (raidFound, False, 0, 0)
        else:
            return (raidFound, False, None, None)

    def detectRaidBoss(self, raidpic, lvl, hash, raidcount):
        foundmon = None
        monID = None
        log.debug('Extracting Raidboss')
        lower = np.array([80, 60, 30], dtype = "uint8")
        upper = np.array([110, 90, 70], dtype = "uint8")
        kernel = np.ones((3,3),np.uint8)
        kernel2 = np.ones((6,6),np.uint8)
        raidMonZoom = cv2.resize(raidpic, (0,0), fx=2, fy=2)
        mask = cv2.inRange(raidMonZoom, lower, upper)
        output = cv2.bitwise_and(raidMonZoom, raidMonZoom, mask = mask)
        monAsset = cv2.inRange(output,np.array([0,0,0]),np.array([15,15,15]))
        monAsset = cv2.morphologyEx(monAsset, cv2.MORPH_CLOSE, kernel)
        monAsset = cv2.morphologyEx(monAsset, cv2.MORPH_OPEN, kernel2)

        picName = self.tempPath + "/" + str(hash) + "_raidboss" + str(raidcount) +".jpg"
        cv2.imwrite(picName, monAsset)

        log.debug('detectRaidBoss: Scanning Raidboss')
        monHash = self.imageHashExists(self.tempPath + "/" + str(hash) + "_raidboss" + str(raidcount) +".jpg", False, 'mon-' + str(lvl))
        log.debug('detectRaidBoss: Monhash: ' + str(monHash))

        if not monHash:
            for file in glob.glob("mon_img/_mon_*_" + str(lvl) + ".png"):
                find_mon = mt.fort_image_matching(file, picName, False, 0.7)
                if foundmon is None or find_mon > foundmon[0]:
                    foundmon = find_mon, file

                if foundmon and foundmon[0]>0.7:
                    monSplit = foundmon[1].split('_')
                    monID = monSplit[3]
                    log.debug('detectRaidBoss: Found mon in mon_img: ' + str(monID))
                    #we found the mon that's most likely to be the one that's in the crop

        else:
            os.remove(picName)
            return monHash, monAsset

        if monID:
            self.imageHash(picName, monID, False, 'mon-' + str(lvl))
            os.remove(picName)
            return monID, monAsset

        os.remove(picName)
        return None, monAsset

    def detectEgg(self, raidpic, hash, raidcount):
        foundegg = None
        eggID = None
        for file in glob.glob("mon_img/_egg_*.png"):
            find_egg = mt.fort_image_matching(file, raidpic, True, 0.9)
            if foundegg is None or find_egg > foundegg[0]:
                foundegg = find_egg, file

            if not foundegg is None and foundegg[0]>0.9:
                eggSplit = foundegg[1].split('_')
                eggID = eggSplit[3]
                log.debug('Eggfound: ' + str(eggID))

        if eggID:
            return eggID

        return False


    def detectLevel(self, raidpic, hash, raidcount):
        foundlvl = None
        lvl = None
        raidlevel = raidpic[200:240, 0:150]
        raidlevel = cv2.resize(raidlevel, (0,0), fx=3, fy=3)

        cv2.imwrite(self.tempPath + "/" + str(hash) + "_raidlevel" + str(raidcount) +".jpg", raidlevel)

        log.debug('Scanning Level')
        for file in glob.glob("mon_img/_raidlevel_*.jpg"):
            find_lvl = mt.fort_image_matching(file, self.tempPath + "/" + str(hash) + "_raidlevel" + str(raidcount) +".jpg", False, 0.9)
            if foundlvl is None or find_lvl > foundlvl[0]:
    	    	foundlvl = find_lvl, file

            if not foundlvl is None and foundlvl[0]>0.9:
                lvlSplit = foundlvl[1].split('_')
                lvl = lvlSplit[3]


        if lvl:
            log.debug("detectLevel: found level '%s'" % str(lvl))
            return lvl
        else:
            log.info("detectLevel: could not find level")
            return None

    def detectGym(self, raidpic, hash, raidcount):
        foundgym = None
        gymId = None

        gymHash = self.imageHashExists(raidpic, True, 'gym')
        #if gymHash is none, we haven't seen the gym yet, otherwise, gymHash == gymId we are looking for
        if gymHash is None:
            for file in glob.glob("gym_img/*.jpg"):
                find_gym = mt.fort_image_matching(raidpic, file, True, 0.8)
                if foundgym is None or find_gym > foundgym[0]:
    	        	foundgym = find_gym, file

                if foundgym and foundgym[0]>=0.8:
                    #okay, we very likely found our gym
                    gymSplit = foundgym[1].split('_')
                    gymId = gymSplit[2]
                    #if we are looking by coords (TODO), we will likely get additional checks somewhere around here and before the for-loop


        else:
            return gymHash

        if gymId:
            self.imageHash(raidpic, gymId, True, 'gym')
            return gymId
        else:
            #we could not find the gym...
            return None

    def unknownfound(self, raidpic, type, zoom, raidcount):
        found = None
        unknownfound = 0
        for file in glob.glob(self.unknownPath + "/" + str(type) + "_*.jpg"):
                    foundunknown = mt.fort_image_matching(raidpic, file, zoom, 0.8)
                    if found is None or foundunknown > found[0]:
        	    		found = foundunknown, file

                    if not found is None and found[0]>=0.8:
                        unknownfound = 1
                        found = None
                        break;

        if unknownfound == 0:
            raidpic = cv2.imread(raidpic)
            cv2.imwrite(self.unknownPath + "/" + str(type) + "_" + str(time.time()) +".jpg", raidpic)

        return True

    def resize(image, width = None, height = None, inter = cv2.INTER_AREA):
        dim = None
        (h, w) = image.shape[:2]
        if width is None and height is None:
            return image
        if width is None:
            r = height / float(h)
            dim = (int(w * r), height)
        else:
            r = width / float(w)
            dim = (width, int(h * r))
        resized = cv2.resize(image, dim, interpolation = inter)
        return resized

    def start_detect(self, filenameOfCrop, hash, raidNo):
        log.debug("start_detect: Starting detection of crop" + str(raidNo))
        if not os.path.isfile(filenameOfCrop):
            log.error("start_detect: File does not exist: %s" % str(filenameOfCrop))
            return

        #gymfound = False
        monfound = False
        eggfound = False

        log.debug("start_detect: Starting analysis of crop %s" % str(raidNo))

        img = cv2.imread(filenameOfCrop)
        img = imutils.resize(img, height=270)
        #img = cv2.resize(img, (176, 270), interpolation = cv2.INTER_CUBIC)
        cv2.imwrite(filenameOfCrop, img)
        img = cv2.imread(filenameOfCrop)

        #get (raidstart, raidend, raidtimer) as (timestamp, timestamp, human-readable hatch)
        raidtimer = self.detectRaidTime(img, hash, raidNo)
        log.debug("start_detect[crop %s]: got raidtime %s" % (str(raidNo), str(raidtimer)))
        #first item in tuple stands for raid present in crop or not
        if (not raidtimer[0]):
            #there is no raid, stop analysis of crop, abandon ship
            os.remove(filenameOfCrop)
            log.debug("start_detect[crop %s]: Crop does not show a raid, stopping analysis" % str(raidNo))
            return False

        #second item is true for egg present, False for mon present
        eggfound = raidtimer[1]
        raidstart = raidtimer[2] #will be 0 if eggfound = False. We report a mon anyway
        raidend = raidtimer[3] #will be 0 if eggfound = False. We report a mon anyway

        #let's get the gym we're likely scanning the image of
        gymId = self.detectGym(filenameOfCrop, hash, raidNo)
        #gymId is either None for Gym not found or contains the gymId as String

        if gymId is None:
            #gym unknown...
            log.warning("start_detect[crop %s]: could not determine gym, aborting analysis" % str(raidNo))
            self.unknownfound(filenameOfCrop, 'gym', True, raidNo)
            os.remove(filenameOfCrop)
            log.debug("start_detect[crop %s]: finished" % str(raidNo))
            return True #return true since a raid is present, we just couldn't find the correct gym

        raidlevel = self.detectLevel(img, hash, raidNo) #we need the raid level to make the possible set of mons smaller
        log.debug("start_detect[crop %s]: determined raidlevel to be %s" % (str(raidNo), str(raidlevel)))
        if raidlevel is None:
            log.error("start_detect[crop %s]: could not determine raidlevel. Filename of Crop: %s" % (str(raidNo), filenameOfCrop))
            return True

        if eggfound:
            log.debug("start_detect[crop %s]: found the crop to contain an egg" % str(raidNo))

            eggId = eggIdsByLevel[int(raidlevel) - 1]
            log.debug("start_detect[crop %s]: Found egg level %s starting at %s and ending at %s. GymID: %s" % (str(raidNo), raidlevel, raidstart, raidend, gymId))
            self.submitRaid(str(gymId), None, raidlevel, raidstart, raidend, 'EGG')
            #guid, pkm, lvl, start, end, type
        else:
            log.debug("start_detect[crop %s]: found the crop to contain a raidboss, let's see what boss it is" % str(raidNo))
            #detectRaidBoss either returns None if the mon cannot be determined or a monID
            monFound = self.detectRaidBoss(img, raidlevel, hash, raidNo)

            if monFound is None:
                #we could not determine the mon... let's move the crop to unknown and stop analysing
                log.error("start_detect[crop %s]: Could not determine mon in crop, aborting and moving crop to unknown" % str(raidNo))
                self.unknownfound(filenameOfCrop, 'mon', False, raidNo)
            else:
                log.debug("start_detect[crop %s]: Submitting mon. ID: %s, gymId: %s" % (str(raidNo), str(monFound[0]), str(gymId)))
                self.submitRaid(str(gymId), monFound[0], raidlevel, None, None, 'MON')

        self.cleanup(filenameOfCrop, hash, raidNo)
        log.debug("start_detect[crop %s]: finished" % str(raidNo))
        return True

    def cleanup(self, filenameOfCrop, hash, raidNo):
        #cleanup
        log.debug('Cleanup')
        os.remove(filenameOfCrop)
        os.remove(self.tempPath + "/" + str(hash) + "_raidlevel" + str(raidNo) + ".jpg")

    def imageHashExists(self, image, zoom, type, hashSize=8):
        dbWrapper = DbWrapper(self.dbIp, self.dbPort, self.dbUser, self.dbPassword, self.dbName, self.timezone)
        image2 = cv2.imread(image,3)
        image2 = cv2.cvtColor(image2, cv2.COLOR_BGR2GRAY)
        if zoom:
            image2 = cv2.resize(image2,None,fx=2, fy=2, interpolation = cv2.INTER_NEAREST)
            crop = image2[int(135):int(200),int(65):int(95)]
        else:
            crop = image2
        resized = cv2.resize(crop, (hashSize + 1, hashSize))
        diff = resized[:, 1:] > resized[:, :-1]
        imageHash = sum([2 ** i for (i, v) in enumerate(diff.flatten()) if v])
        existHash = dbWrapper.checkForHash( str(imageHash), str(type) )
        if not existHash:
            log.debug('Hash not exists')
            return None
        log.debu(existHash)
        return existHash

    def imageHash(self, image, id, zoom, type, hashSize=8):
        dbWrapper = DbWrapper(self.dbIp, self.dbPort, self.dbUser, self.dbPassword, self.dbName, self.timezone)
        image2 = cv2.imread(image,3)
        image2 = cv2.cvtColor(image2, cv2.COLOR_BGR2GRAY)
        if zoom:
            image2 = cv2.resize(image2,None,fx=2, fy=2, interpolation = cv2.INTER_NEAREST)
            crop = image2[int(135):int(200),int(65):int(95)]
        else:
            crop = image2

        resized = cv2.resize(crop, (hashSize + 1, hashSize))
        diff = resized[:, 1:] > resized[:, :-1]
        imageHash = sum([2 ** i for (i, v) in enumerate(diff.flatten()) if v])
        log.debug('Adding Hash to Database')
        log.debug({'type': str(type),'hash': str(imageHash), 'id': str(id)})
        dbWrapper.insertHash(str(imageHash), str(type), str(id))

def checkHourMin(hour_min):
        hour_min[0] = unicode(hour_min[0].replace('O','0').replace('o','0').replace('A','4'))
        hour_min[1] = unicode(hour_min[1].replace('O','0').replace('o','0').replace('A','4'))
        if (hour_min[0]).isnumeric()==True and (hour_min[1]).isnumeric()==True:
            return True, hour_min
        else:
            return False, hour_min

def getHatchTime(self,data):
        zero = datetime.datetime.now().replace(hour=0,minute=0,second=0,microsecond=0)
        unix_zero =  time.mktime(zero.timetuple())
        hour_min_divider = data.find(':')
        if hour_min_divider != -1:
            AM = data.find('AM')
            PM = data.find('PM')
            if AM >= 4:
                data = data.replace('A','').replace('M','').replace('~','').replace('-','').replace(' ','')
                hour_min = data.split(':')
                ret, hour_min = checkHourMin(hour_min)
                if ret == True:
                    return int(unix_zero)+int(hour_min[0])*3600+int(hour_min[1])*60
                else:
                    return False
            elif PM >= 4:
                data = data.replace('P','').replace('M','').replace('~','').replace('-','').replace(' ','')
                hour_min = data.split(':')
                ret, hour_min = checkHourMin(hour_min)
                if ret == True:
                    if hour_min[0] == '12':
                        return int(unix_zero)+int(hour_min[0])*3600+int(hour_min[1])*60
                    else:
                        return int(unix_zero)+(int(hour_min[0])+12)*3600+int(hour_min[1])*60
                else:
                    return False
            else:
                data = data.replace('~','').replace('-','').replace(' ','')
                hour_min = data.split(':')
                ret, hour_min = checkHourMin(hour_min)
                if ret == True:
                    return int(unix_zero)+int(hour_min[0])*3600+int(hour_min[1])*60
                else:
                    return False
        else:
            return False

if __name__ == '__main__':
    scanner = Scanner(args.dbip, args.dbport, args.dbusername, args.dbpassword, args.dbname, args.temp_path, args.unknown_path, args.timezone)
    scanner.start_detect('1080_02.png', '12313231331213', 1)
