# -*- coding: utf-8 -*-

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
import json
import hashlib
import re

import sys
reload(sys)
sys.setdefaultencoding('utf8')

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

        self.dbWrapper = DbWrapper(self.dbIp, self.dbPort, self.dbUser, self.dbPassword, self.dbName, self.timezone)

        if not os.path.exists(self.tempPath):
            log.info('Temp directory created')
            os.makedirs(self.tempPath)

        if not os.path.exists(self.unknownPath):
            log.info('Unknow directory created')
            os.makedirs(self.unknownPath)

    def detectRaidTime(self, raidpic, hash, raidNo):
        log.debug('Reading Raidtimer')
        raidtimer = raidpic[200:230, 30:150]
        emptyRaidTempPath = self.tempPath + "/" + str(raidNo) + str(hash) + "_emptyraid.png"
        cv2.imwrite(emptyRaidTempPath, raidtimer)
        rt = Image.open(emptyRaidTempPath)
        gray = rt.convert('L')
        bw = gray.point(lambda x: 0 if x<200 else 255, '1')
        raidtimer = pytesseract.image_to_string(bw, config='--psm 6 --oem 3').replace(' ', '').replace('~','').replace('o','0').replace('O','0').replace('-','').replace('.',':')
        log.debug(raidtimer)
        #log.debug(re.match(r'\d\d:\d\d[am|pm]*', raidtimer))
        #cleanup
        os.remove(emptyRaidTempPath)
        raidFound = len(raidtimer) > 0

        if raidFound:
            if ':' in raidtimer:
                now = datetime.datetime.now()
                log.info("getHatchTime: found raidtimer '%s'" % raidtimer)
                hatchTime = self.getHatchTime(raidtimer)
                if hatchTime:
                    log.info("getHatchTime: Hatchtime %s" % str(hatchTime))
                    #raidstart = getHatchTime(self, raidtimer) - self.timezone * (self.timezone*60*60)
                    raidstart = hatchTime - (self.timezone * 60 * 60)
                    raidend = hatchTime + 45 * 60 - (self.timezone * 60 * 60)
                    #raidend = getHatchTime(self, raidtimer) + int(45*60) - (self.timezone*60*60)
                    log.debug('Start: ' + str(raidstart) + ' End: ' + str(raidend))
                    return (raidFound, True, raidstart, raidend)
                else:
                    return (raidFound, True, False, False)

            else:
                return (raidFound, False, '0', '0')
        else:
            return (raidFound, False, False, False)

    def detectRaidEndtimer(self, raidpic, hash, raidNo):
        log.debug('Reading Raidtimer')
        raidtimer = raidpic[178:200, 45:130]
        emptyRaidTempPath = self.tempPath + "/" + str(raidNo) + str(hash) + "_endraid.png"
        cv2.imwrite(emptyRaidTempPath, raidtimer)
        rt = Image.open(emptyRaidTempPath)
        gray = rt.convert('L')
        bw = gray.point(lambda x: 0 if x<200 else 255, '1')

        
        raidtimer = pytesseract.image_to_string(bw, config='--psm 6 --oem 3').replace(' ', '').replace('~','').replace('o','0').replace('O','0').replace('-','').replace('.',':').replace('B','8').replace('A','4').replace('—','')
        log.debug('Raid-End-Text: ' + str(raidtimer))

        os.remove(emptyRaidTempPath)
        raidEndFound = len(raidtimer) > 0

        if raidEndFound:
            if ':' in raidtimer:
                now = datetime.datetime.now()
                log.info("detectRaidEndtimer: found raidendtimer '%s'" % raidtimer)
                endTime = self.getEndTime(raidtimer)
                if endTime:
                    log.info("detectRaidEndtimer: Endtime %s" % str(endTime))
                    #raidstart = getHatchTime(self, raidtimer) - self.timezone * (self.timezone*60*60)
                    raidend = endTime  - (self.timezone * 60 * 60)
                    #raidend = getHatchTime(self, raidtimer) + int(45*60) - (self.timezone*60*60)
                    log.debug(' End: ' + str(raidend))
                    return (raidEndFound, True, raidend)
                else:
                    return (raidEndFound, False, False)

            else:
                return (raidEndFound, False, '0')
        else:
            return (raidEndFound, False, False)

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
        monHash = self.imageHashExists(self.tempPath + "/" + str(hash) + "_raidboss" + str(raidcount) +".jpg", False, 'mon-' + str(lvl), raidcount)
        log.debug('detectRaidBoss: Monhash: ' + str(monHash))

        if monHash is None:
            for file in glob.glob("mon_img/_mon_*_" + str(lvl) + ".png"):
                
                find_mon = mt.fort_image_matching(file, picName, False, 0.75)

                if foundmon is None or find_mon > foundmon[0]:
                    foundmon = find_mon, file

                if foundmon and foundmon[0]>0.75:
                    monSplit = foundmon[1].split('_')
                    monID = monSplit[3]

            #we found the mon that's most likely to be the one that's in the crop
            log.debug('detectRaidBoss: Found mon in mon_img: ' + str(monID))

        else:
            os.remove(picName)
            return monHash, monAsset

        if monID:
            self.imageHash(picName, monID, False, 'mon-' + str(lvl), raidcount)
            os.remove(picName)
            return monID, monAsset

        log.debug('No Mon found!')

        os.remove(picName)
        return False, monAsset

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
        lvlTypes = ['mon_img/_raidlevel_5_.jpg', 'mon_img/_raidlevel_4_.jpg',
                    'mon_img/_raidlevel_3_.jpg', 'mon_img/_raidlevel_2_.jpg',
                    'mon_img/_raidlevel_1_.jpg']

        raidlevel = raidpic[230:260, 0:170]
        #raidlevel = cv2.resize(raidlevel, (0,0), fx=2, fy=2)

        cv2.imwrite(self.tempPath + "/" + str(hash) + "_raidlevel" + str(raidcount) +".jpg", raidlevel)

        log.debug('Scanning Level')
        for file in lvlTypes:
            find_lvl = mt.fort_image_matching(file, self.tempPath + "/" + str(hash) + "_raidlevel" + str(raidcount) +".jpg", False, 0.7)

            if foundlvl is None or find_lvl > foundlvl[0]:
    	    	foundlvl = find_lvl, file

            if not foundlvl is None and foundlvl[0]>0.7:
                lvlSplit = foundlvl[1].split('_')
                lvl = lvlSplit[3]


        os.remove(self.tempPath + "/" + str(hash) + "_raidlevel" + str(raidcount) + ".jpg")

        if lvl:
            log.debug("detectLevel: found level '%s'" % str(lvl))
            return lvl
        else:
            log.info("detectLevel: could not find level")
            return None

    def detectGym(self, raidpic, hash, raidcount, captureLat, captureLng, monId = None):
        foundgym = None
        gymId = None
        x1 = 50
        x2 = 80
        y1 = 100
        y2 = 160
        foundMonCrops = False


        #if gymHash is none, we haven't seen the gym yet, otherwise, gymHash == gymId we are looking for
        if monId:
            log.debug('Got Mon-ID for Gym-Detection %s' % monId)
            with open('monsspec.json') as f:
                data = json.load(f)

            if str(monId) in data:
                foundMonCrops = True
                crop = data[str(monId)]["Crop"]
                log.debug('Found other Crops for Mon %s' % monId)
                log.debug(str(crop))
                x1 = crop['X1']
                x2 = crop['X2']
                y1 = crop['Y1']
                y2 = crop['Y2']

        gymHash = self.imageHashExists(raidpic, True, 'gym', raidcount, x1, x2, y1, y2)

        if gymHash is None:
            
            log.debug('Searching closest gyms')
            closestGymIds = self.dbWrapper.getNearGyms(captureLat, captureLng)
            
            log.debug('start_detect[crop ' + str(raidcount) + ']: Detecting Gym')
            for closegym in closestGymIds:
                
                for file in glob.glob("gym_img/*" + closegym[0] + "*.jpg"):
                    find_gym = mt.fort_image_matching(raidpic, file, True, 0.65, x1, x2, y1, y2)
                    log.debug("Compare Gym-ID - " + str(closegym[0]) + " - Match: " + str(find_gym))
                    if foundgym is None or find_gym > foundgym[0]:
    	        	    foundgym = find_gym, file

                    if foundgym and foundgym[0]>=0.65:
                        #okay, we very likely found our gym
                        gymSplit = foundgym[1].split('_')
                        gymId = gymSplit[2]

        else:
            return gymHash

        if gymId:
            if foundMonCrops:
                log.debug('Dont hash Gym with spec. Crops')
            else:
                self.imageHash(raidpic, gymId, True, 'gym', raidcount, x1, x2, y1, y2)
                
            return gymId
        else:
            #we could not find the gym...
            return None

    def unknownfound(self, raidpic, type, zoom, raidcount, lat=0, lng=0):
        raidpic = cv2.imread(raidpic)
        cv2.imwrite(self.unknownPath + "/" + str(type) + "_" + str(lat) + "_" + str(lng) + "_" + str(time.time()) +".jpg", raidpic)
        return True


    def decodeHashJson(self, hashJson):
        data = json.loads(hashJson)
        log.debug('Decoding Raid Hash Json')
        log.debug(data)

        raidGym = data['gym']
        raidLvl = data["lvl"]
        raidMon = data["mon"]

        return raidGym, raidLvl, raidMon

    def encodeHashJson(self, gym, lvl, mon):
        log.debug('Encoding Raid Hash Json')
        hashJson = json.dumps({'gym': gym, 'lvl': lvl, 'mon': mon, 'lvl': lvl}, separators=(',',':'))
        log.debug(hashJson)
        return hashJson
        
    def cropImage(self, image):
        gray=cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
        edged = cv2.Canny(image, 10, 250)
        (cnd, cnts, _) = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        idx = 0
        for c in cnts:
            log.debug(cv2.boundingRect(c))
            x,y,w,h = cv2.boundingRect(c)
            if x<20 and y<25:
                idx+=1
                new_img=image[y:y+h,x:x+w]
                return new_img
        
        

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

    def start_detect(self, filenameOfCrop, hash, raidNo, captureTime, captureLat, captureLng):
        log.debug("start_detect: Starting detection of crop" + str(raidNo))
        if not os.path.isfile(filenameOfCrop):
            log.error("start_detect: File does not exist: %s" % str(filenameOfCrop))
            return

        monfound = False
        eggfound = False

        log.debug("start_detect: Starting analysis of crop %s" % str(raidNo))

        img = cv2.imread(filenameOfCrop)
        img = imutils.resize(img, height=270)
        cv2.imwrite(filenameOfCrop, img)
        img = cv2.imread(filenameOfCrop)

        raidhash = img[0:175, 0:170]
        raidhash = self.cropImage(raidhash)
        raidhashPic = self.tempPath + "/" + str(hash) + "_raidhash" + str(raidNo) +".jpg"
        cv2.imwrite(raidhashPic, raidhash)

        #get (raidstart, raidend, raidtimer) as (timestamp, timestamp, human-readable hatch)
        raidtimer = self.detectRaidTime(img, hash, raidNo)
        log.debug("start_detect[crop %s]: got raidtime %s" % (str(raidNo), str(raidtimer)))
        #first item in tuple stands for raid present in crop or not
        if (not raidtimer[0]):
            #there is no raid, stop analysis of crop, abandon ship
            os.remove(filenameOfCrop)
            os.remove(raidhashPic)
            log.debug("start_detect[crop %s]: Crop does not show a raid, stopping analysis" % str(raidNo))
            return False

        #second item is true for egg present, False for mon present
        eggfound = raidtimer[1]
        raidstart = raidtimer[2] #will be 0 if eggfound = False. We report a mon anyway
        raidend = raidtimer[3] #will be 0 if eggfound = False. We report a mon anyway

        if (not raidstart or not raidend):
            #there is no raid, stop analysis of crop, abandon ship
            os.remove(filenameOfCrop)
            os.remove(raidhashPic)
            log.debug("start_detect[crop %s]: Crop does not show a valid time, stopping analysis" % str(raidNo))
            return False

        log.debug('Creating Hash overall')
        #raidHash = self.imageHashExists(raidhashPic, False, 'raid', raidNo)
        raidHash = False
        log.debug('detectRaidHash: ' + str(raidHash))

        if raidHash:
            raidHash = self.decodeHashJson(raidHash)
            gym = raidHash[0]
            lvl = raidHash[1]
            mon = raidHash[2]

            #if lvl != raidlevel:
            #    log.debug('Scanned Raidlevel is different to hash - taking scanned level')
            #    lvl = raidlevel

            if not mon:
                log.debug('Found Raidhash with an egg - fast submit')
                log.debug("start_detect[crop %s]: Found egg level %s starting at %s and ending at %s. GymID: %s" % (str(raidNo), lvl, raidstart, raidend, gym))
                self.dbWrapper.submitRaid(str(gym), None, lvl, raidstart, raidend, 'EGG')
            else:
                log.debug('Found Raidhash with an mon - fast submit')
                log.debug("start_detect[crop %s]: Submitting mon. ID: %s, gymId: %s" % (str(raidNo), str(mon), str(gym)))
                self.dbWrapper.submitRaid(str(gym), mon, lvl, None, None, 'MON')
            os.remove(filenameOfCrop)
            os.remove(raidhashPic)
            log.debug("start_detect[crop %s]: finished" % str(raidNo))
            return True

        raidlevel = self.detectLevel(img, hash, raidNo) #we need the raid level to make the possible set of mons smaller
        log.debug("start_detect[crop %s]: determined raidlevel to be %s" % (str(raidNo), str(raidlevel)))

        if raidlevel is None:
            log.error("start_detect[crop %s]: could not determine raidlevel. Filename of Crop: %s" % (str(raidNo), filenameOfCrop))
            os.remove(filenameOfCrop)
            os.remove(raidhashPic)
            return True

        if eggfound:
            log.debug("start_detect[crop %s]: found the crop to contain an egg" % str(raidNo))
            eggId = eggIdsByLevel[int(raidlevel) - 1]

        if not eggfound:
            log.debug("start_detect[crop %s]: found the crop to contain a raidboss, let's see what boss it is" % str(raidNo))
            monFound = self.detectRaidBoss(img, raidlevel, hash, raidNo)
            if not monFound[0]:
                #we could not determine the mon... let's move the crop to unknown and stop analysing
                log.error("start_detect[crop %s]: Could not determine mon in crop, aborting and moving crop to unknown" % str(raidNo))
                self.unknownfound(filenameOfCrop, 'mon', False, raidNo, captureLat, captureLng)
                log.warning("start_detect[crop %s]: could not determine mon, aborting analysis" % str(raidNo))
                os.remove(raidhashPic)
                os.remove(filenameOfCrop)
                return True
            log.debug('Scanning Mon')
            gymId = self.detectGym(raidhashPic, hash, raidNo, captureLat, captureLng, monFound[0])

        else:
            #let's get the gym we're likely scanning the image of
            gymId = self.detectGym(raidhashPic, hash, raidNo, captureLat, captureLng)
            #gymId is either None for Gym not found or contains the gymId as String

        if gymId is None:
            #gym unknown...
            log.warning("start_detect[crop %s]: could not determine gym, aborting analysis" % str(raidNo))
            self.unknownfound(filenameOfCrop, 'gym', False, raidNo, captureLat, captureLng)
            os.remove(filenameOfCrop)
            os.remove(raidhashPic)
            log.debug("start_detect[crop %s]: finished" % str(raidNo))
            return True #return true since a raid is present, we just couldn't find the correct gym

        if eggfound:
            log.debug("start_detect[crop %s]: Found egg level %s starting at %s and ending at %s. GymID: %s" % (str(raidNo), raidlevel, raidstart, raidend, gymId))
            self.dbWrapper.submitRaid(str(gymId), None, raidlevel, raidstart, raidend, 'EGG')
            raidHashJson = self.encodeHashJson(gymId, raidlevel, False)
            log.debug('Adding Raidhash to Database')
            self.imageHash(raidhashPic, raidHashJson, False, 'raid', raidNo)
            #guid, pkm, lvl, start, end, type

        else:
            log.debug('Checking for Endtime')
            if not self.dbWrapper.readRaidEndtime(str(gymId)):
                log.debug('No Egg found')
                raidend = self.detectRaidEndtimer(img, hash, raidNo)
                log.debug(raidend)
                if raidend[1]:
                    log.debug(raidend[2])
                    log.debug("start_detect[crop %s]: Submitting mon. ID: %s, gymId: %s" % (str(raidNo), str(monFound[0]), str(gymId)))
                    self.dbWrapper.submitRaid(str(gymId), monFound[0], raidlevel, None, raidend[2], 'MON', True)
            else:
                log.debug('Egg found')
                log.debug("start_detect[crop %s]: Submitting mon. ID: %s, gymId: %s" % (str(raidNo), str(monFound[0]), str(gymId)))
                self.dbWrapper.submitRaid(str(gymId), monFound[0], raidlevel, None, None, 'MON')

            raidHashJson = self.encodeHashJson(gymId, raidlevel, monFound[0])
            log.debug('Adding Raidhash to Database')
            self.imageHash(raidhashPic, raidHashJson, False, 'raid', raidNo)

        os.remove(raidhashPic)
        os.remove(filenameOfCrop)

        log.debug("start_detect[crop %s]: finished" % str(raidNo))
        return True
        
        
    def dhash(self, image, hash_size = 8):
                # Grayscale and shrink the image in one step.
        image = image.convert('L').resize(
            (hash_size + 1, hash_size),
            Image.ANTIALIAS,
        )
        pixels = list(image.getdata())
        # Compare adjacent pixels.
        difference = []
        for row in xrange(hash_size):
            for col in xrange(hash_size):
                pixel_left = image.getpixel((col, row))
                pixel_right = image.getpixel((col + 1, row))
                difference.append(pixel_left > pixel_right)
        # Convert the binary array to a hexadecimal string.
            decimal_value = 0
            hex_string = []
            for index, value in enumerate(difference):
                if value:
                    decimal_value += 2**(index % 8)
                if (index % 8) == 7:
                    hex_string.append(hex(decimal_value)[2:].rjust(2, '0'))
                    decimal_value = 0
                    
        hashValue = ''.join(hex_string)
        log.debug('Hash: ' + str(hashValue))
        
        return hashValue
            

    def imageHashExists(self, image, zoom, type, raidNo, x1=50, x2=80, y1=100, y2=160, hashSize=8):
        image2 = cv2.imread(image,3)
        image2 = cv2.cvtColor(image2, cv2.COLOR_BGR2GRAY)
        if zoom:
            image2 = cv2.resize(image2,None,fx=2, fy=2, interpolation = cv2.INTER_NEAREST)
            crop = image2[int(y1):int(y2),int(x1):int(x2)]
        else:
            crop = image2
            
        tempHash = self.tempPath + "/" + str(time.time()) + "_" + str(raidNo) + "temphash.jpg"
        cv2.imwrite(tempHash, crop) 
        hashPic = Image.open(tempHash)

        #resized = cv2.resize(crop, (hashSize + 1, hashSize))
        #diff = resized[:, 1:] > resized[:, :-1]
        #imageHash = sum([2 ** i for (i, v) in enumerate(diff.flatten()) if v])
        imageHash = self.dhash(hashPic)
        
        os.remove(tempHash)
        
        existHash = self.dbWrapper.checkForHash(str(imageHash), str(type))
        if not existHash:
            log.debug('Hash not found')
            return None
        log.debug('Hash found: %s' % existHash)
        return existHash

    def imageHash(self, image, id, zoom, type, raidNo, x1=50, x2=80, y1=100, y2=160, hashSize=8):
        image2 = cv2.imread(image,3)
        image2 = cv2.cvtColor(image2, cv2.COLOR_BGR2GRAY)
        if zoom:
            image2 = cv2.resize(image2,None,fx=2, fy=2, interpolation = cv2.INTER_NEAREST)
            crop = image2[int(y1):int(y2),int(x1):int(x2)]
        else:
            crop = image2
            
        tempHash = self.tempPath + "/" + str(time.time()) + "_" + str(raidNo) + "temphash.jpg"
        cv2.imwrite(tempHash, crop) 
        hashPic = Image.open(tempHash)

        #resized = cv2.resize(crop, (hashSize + 1, hashSize))
        #diff = resized[:, 1:] > resized[:, :-1]
        #imageHash = sum([2 ** i for (i, v) in enumerate(diff.flatten()) if v])
        imageHash = self.dhash(hashPic)
        
        os.remove(tempHash)

        log.debug('Adding Hash to Database')
        log.debug({'type': str(type),'hash': str(imageHash), 'id': str(id)})
        self.dbWrapper.insertHash(str(imageHash), str(type), str(id))

    def checkHourMin(self, hour_min):
        hour_min[0] = unicode(hour_min[0].replace('O','0').replace('o','0').replace('A','4'))
        hour_min[1] = unicode(hour_min[1].replace('O','0').replace('o','0').replace('A','4'))
        if (hour_min[0]).isnumeric()==True and (hour_min[1]).isnumeric()==True:
            return True, hour_min
        else:
            return False, hour_min

    def checkHourMinSec(self, hour_min_sec):
        hour_min_sec[0] = unicode(hour_min_sec[0].replace('O','0').replace('o','0').replace('A','4'))
        hour_min_sec[1] = unicode(hour_min_sec[1].replace('O','0').replace('o','0').replace('A','4'))
        hour_min_sec[2] = unicode(hour_min_sec[2].replace('O','0').replace('o','0').replace('A','4'))
        if (hour_min_sec[0]).isnumeric()==True and (hour_min_sec[1]).isnumeric()==True and (hour_min_sec[2]).isnumeric()==True:
            return True, hour_min_sec
        else:
            return False, hour_min_sec

    def getHatchTime(self,data):
        zero = datetime.datetime.now().replace(hour=0,minute=0,second=0,microsecond=0)
        unix_zero =  time.mktime(zero.timetuple())
        hour_min_divider = data.find(':')
        if hour_min_divider is None or hour_min_divider == -1:
            return False

        #TODO: think about only one big fat regex noone wants to read lateron
        am_found = re.search(r'[a|A]\w+', data)
        pm_found = re.search(r'[p|P]\w+', data)
        hour_min = re.search(r'([\d]{1,2}:[\d]{1,2})', data)

        if hour_min is None:
            log.fatal("getHatchTime: Could not locate a HH:MM")
            return False
        else:
            hour_min = hour_min.group(1).split(':')

        ret, hour_min = self.checkHourMin(hour_min)
        if not ret:
            return False

        if am_found:
            log.debug('Found AM')
            return int(unix_zero)+int(hour_min[0])*3600+int(hour_min[1])*60
        elif pm_found:
            log.debug('Found PM')
            if hour_min[0] == '12':
                return int(unix_zero)+int(hour_min[0])*3600+int(hour_min[1])*60
            else:
                return int(unix_zero)+(int(hour_min[0])+12)*3600+int(hour_min[1])*60
        else:
            log.debug('Found EU Time')
            return int(unix_zero)+int(hour_min[0])*3600+int(hour_min[1])*60

    def getEndTime(self, data):
        zero = datetime.datetime.now()
        unix_zero =  time.mktime(zero.timetuple())
        hour_min_divider = data.find(':')
        log.debug(':Count: ' + str(data.count(':')))
        if data.count(':') < 2 :
            log.error('Detect wrong Endtimer of Raid')
            return False
        if hour_min_divider != -1:
            data = data.replace('~','').replace('-','').replace(' ','')
            hour_min = data.split(':')
            ret, hour_min = self.checkHourMinSec(hour_min)
            if ret == True:
                return int(unix_zero)+int(hour_min[0])*3600+int(hour_min[1])*60+int(hour_min[2])
            else:
                return False
        else:
            return False

if __name__ == '__main__':
    scanner = Scanner(args.dbip, args.dbport, args.dbusername, args.dbpassword, args.dbname, args.temp_path, args.unknown_path, args.timezone)
    test = scanner.start_detect('crop2_new.png', '123123123', 1)
    print test
