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

log = logging.getLogger(__name__)
args = parseArgs()

monegg = []
monegg.append(args.egg1_mon_id)
monegg.append(args.egg2_mon_id)
monegg.append(args.egg3_mon_id)
monegg.append(args.egg4_mon_id)
monegg.append(args.egg5_mon_id)

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

        if not os.path.exists('hash'):
            log.info('Hash directory created')
            os.makedirs('hash')

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
        log.error("Submitting something of type %s" % type)
        if type == 'EGG':
            #query = " UPDATE raid SET level = %s, spawn=FROM_UNIXTIME(%s), start=FROM_UNIXTIME(%s), end=FROM_UNIXTIME(%s), pokemon_id = %s, cp = %s, move_1 = %s, move_2 = %s, last_scanned = %s WHERE gym_id = %s "
            #data = (lvl, start, start, end, monegg[int(lvl) - 1], "999", "1", "1",  today1, guid)
            log.info("Submitting Egg. Gym: %s, Lv: %s, Start and Spawn: %s, End: %s, last_scanned: %s" % (guid, lvl, start, end, today1))
            query = (' INSERT INTO raid (gym_id, level, spawn, start, end, pokemon_id, cp, move_1, ' +
                'move_2, last_scanned) VALUES(%s, %s, FROM_UNIXTIME(%s), FROM_UNIXTIME(%s), ' +
                'FROM_UNIXTIME(%s), %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE level = %s, ' +
                'spawn=FROM_UNIXTIME(%s), start=FROM_UNIXTIME(%s), end=FROM_UNIXTIME(%s), ' +
                'pokemon_id = %s, cp = %s, move_1 = %s, move_2 = %s, last_scanned = %s')
            data = (guid, lvl, start, start, end, pkm, "999", "1", "1", today1,
                lvl, start, start, end, pkm, "999", "1", "1", today1)
            #data = (lvl, start, start, end, None, "999", "1", "1", today1, guid)
            cursor.execute(query, data)
        else:
            log.error("Submitting mon. PokemonID %s, Lv %s, last_scanned %s, gymID %s" % (pkm, lvl, today1, guid))
            query = " UPDATE raid SET level = %s, pokemon_id = %s, cp = %s, move_1 = %s, move_2 = %s, last_scanned = %s WHERE gym_id = %s "
            data = (lvl, pkm, "999", "1", "1",  today1, guid)
            cursor.execute(query, data)

        connection.commit()
        return 0

    def detectRaidTime(self, raidpic, hash):
        log.debug('Reading Raidtimer')
        raidtimer = raidpic[180:210, 0:297]
        raidtimer = cv2.resize(raidtimer, (0,0), fx=3, fy=3)
        cv2.imwrite(self.tempPath + "/" + str(hash) + "_emptyraid.png", raidtimer)
        rt = Image.open(self.tempPath + "/" + str(hash) + "_emptyraid.png")
        gray = rt.convert('L')
        bw = gray.point(lambda x: 0 if x<210 else 255, '1')
        raidtimer = pytesseract.image_to_string(bw, config='-psm 7').replace(' ', '').replace('~','').replace('o','0').replace('O','0').replace('-','')
        log.debug(raidtimer)
        
        if "R" not in raidtimer:
            now = datetime.datetime.now()

            raidstart = getHatchTime(self, raidtimer)
            raidend = getHatchTime(self, raidtimer) + int(45*60)

            log.debug('Start: ' + str(raidstart) + ' End: ' + str(raidend))
            return raidstart, raidend, raidtimer
        else:
            return 0, 0, raidtimer
        return False
        
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
        
        log.error('Scanning Raidboss')
        monHash = self.imageHashExists(self.tempPath + "/" + str(hash) + "_raidboss" + str(raidcount) +".jpg", False, 'mon-' + str(lvl))
        log.debug('Monhash: ' + str(monHash))
        
        if not monHash:
            for file in glob.glob("mon_img/_mon_*_" + str(lvl) + ".png"):
                find_mon = mt.fort_image_matching(file, picName, False, 0.7)
                if foundmon is None or find_mon > foundmon[0]:
                    foundmon = find_mon, file

                if not foundmon is None and foundmon[0]>0.7:
                    monSplit = foundmon[1].split('_')
                    monID = monSplit[3]
                    
            
        else:
            return monHash, monAsset
         
        if monID:
            self.imageHash(picName, monID, False, 'mon-' + str(lvl))
            return monID, monAsset    
            
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
        raidlevel = raidpic[210:240, 0:297]
        raidlevel = cv2.resize(raidlevel, (0,0), fx=3, fy=3)
        
        cv2.imwrite(self.tempPath + "/" + str(hash) + "_raidlevel" + str(raidcount) +".jpg", raidlevel)
        
        log.debug('Scanning Level')
        for file in glob.glob("mon_img/_raidlevel_*.jpg"):
            find_lvl = mt.fort_image_matching(file, self.tempPath + "/" + str(hash) + "_raidlevel" + str(raidcount) +".jpg", False, 0.5)
            if foundlvl is None or find_lvl > foundlvl[0]:
    	    	foundlvl = find_lvl, file

            if not foundlvl is None and foundlvl[0]>0.5:
                lvlSplit = foundlvl[1].split('_')
                lvl = lvlSplit[3]
                log.debug('Level: ' + str(lvl))
        
        if lvl:
            return lvl
            
        return False

    def detectGym(self, raidpic, hash, raidcount):
        foundgym = None
        gymID = None

        gymHash = self.imageHashExists(raidpic, True, 'gym')
        if not gymHash:
            for file in glob.glob("gym_img/*.jpg"):
                find_gym = mt.fort_image_matching(raidpic, file, True, 0.55)
                print find_gym
                if foundgym is None or find_gym > foundgym[0]:
    	        	foundgym = find_gym, file

                if not foundgym is None and foundgym[0]>0.55:
                    gymSplit = foundgym[1].split('_')
                    gymID = gymSplit[2]
                    
        else:
            return gymHash
         
        if gymID:
            self.imageHash(raidpic, gymID, True, 'gym')
            return gymID
            
        return False


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

    def start_detect(self, filename, hash, RaidNo):
        log.error("Starting detection")
        if not os.path.isfile(filename):
            log.error("File does not exist")
            log.error(filename)
            return
            
        gymfound = False
        monfound = False
        eggfound = False

        log.error("Starting analisys")

        img = cv2.imread(filename)
        img = imutils.resize(img, height=270)
        #img = cv2.resize(img, (176, 270), interpolation = cv2.INTER_CUBIC)
        cv2.imwrite(filename, img)
        img = cv2.imread(filename) 
            
        raidtimer = self.detectRaidTime(img, hash)
        
        if len(raidtimer[2]) > 0:
            
            raidstart = raidtimer[0]
            raidend = raidtimer[1]
            
            detectLevel = self.detectLevel(img, hash, RaidNo)
            detectEgg = self.detectEgg(filename, hash, RaidNo)
            if detectEgg:
                eggfound = True
            else:     
                detectRaidBoss = self.detectRaidBoss(img, detectLevel, hash, RaidNo)
                if detectRaidBoss[0]:
                    detectRaidBoss = detectRaidBoss[0]
                    detectRaidBossBW = detectRaidBoss[1]
                    monfound = True
                else:
                    detectRaidBossBW = detectRaidBoss[1]
                
            detectGym = self.detectGym(filename, hash, RaidNo)
            
            if detectGym and eggfound:
                logtext = 'Egg - ID: ' + str(detectEgg)
                log.debug("Found egg Lv %s starting at %s and ending at %s. GymID: %s" % (detectEgg, raidstart, raidend, detectGym))
                self.submitRaid(str(detectGym), monegg[int(detectLevel)-1], detectLevel, raidstart, raidend, 'EGG')
                print("Raid %s | Gym-ID: %s | %s | Level: %s" % (RaidNo, detectGym, logtext, detectLevel))
                
            if detectGym and monfound:
                logtext = 'Mon - ID: ' + str(detectRaidBoss)
                self.submitRaid(str(detectGym), detectRaidBoss, detectLevel, '-', '-', 'MON')
                print("Raid %s | Gym-ID: %s | %s | Level: %s" % (RaidNo, detectGym, logtext, detectLevel))
             
            if detectGym and (not monfound and not eggfound):
                logtext = 'Mon or Egg unknown'
                self.unknownfound(filename, 'mon', False, RaidNo)
                print("Raid %s | Gym-ID: %s | %s | Level: %s" % (RaidNo, detectGym, logtext, detectLevel))
                
                
            if not detectGym and (monfound or eggfound):
                logtext = 'Gym unknown'
                if monfound:
                    logtext_add = 'Mon - ID: ' + str(detectRaidBoss)
                else:
                    logtext_add = 'Egg - ID: ' + str(detectEgg)
                self.unknownfound(filename, 'gym', True, RaidNo)
                print("Raid %s | %s | %s | Level: %s" % (RaidNo, logtext, logtext_add, detectLevel))
                
            if not detectGym and not monfound and not eggfound:
                logtext = 'Gym unknown & Mon/Egg unknown'
                self.unknownfound(filename, 'gym', True, RaidNo)
                self.unknownfound(filename, 'mon', False, RaidNo)
                print("Raid %s | %s | Level: %s" % (RaidNo, logtext, detectLevel))
                
        else:
            os.remove(filename)
            if RaidNo == 1:
                log.error('No active Raids')
                return False
            else:
                log.error('No more active Raids')
                return False  
                
        #os.remove(filename)
        #os.remove(self.tempPath + "/" + str(hash) + "_emptyraid.png")
        #os.remove(self.tempPath + "/" + str(hash) + "_raidlevel" + str(RaidNo) + ".jpg")
        return True

    def imageHashExists(self, image, zoom, type, hashSize=8):
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
        log.debug('hash/_' + str(imageHash) + '_*_' + str(type) + '_')
        for file in glob.glob('hash/_' + str(imageHash) + '_*_' + str(type) + '_'):
            log.debug(file)
            Split = file.split('_')
            log.debug(Split)
            return Split[2]

        return False

    def imageHash(self, image, id, zoom, type, hashSize=8):
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
        file = open('hash/_' + str(imageHash) + '_' + str(id) + '_' + str(type) + '_','w')
        file.write(id)
        file.close()

def checkHourMin(hour_min):
        hour_min[0] = unicode(hour_min[0].replace('O','0').replace('o','0').replace('A','4'))
        hour_min[1] = unicode(hour_min[1].replace('O','0').replace('o','0').replace('A','4'))
        if (hour_min[0]).isnumeric()==True and (hour_min[1]).isnumeric()==True:
            return True, hour_min
        else:
            return False, hour_min

def getHatchTime(self,data):
        zero = datetime.datetime.now().replace(hour=0,minute=0,second=0,microsecond=0)
        unix_zero = (zero-datetime.datetime(1970,1,1)).total_seconds()
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
                    return -1
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
                    return -1
            else:
                data = data.replace('~','').replace('-','').replace(' ','')
                hour_min = data.split(':')
                ret, hour_min = checkHourMin(hour_min)
                if ret == True:
                    return int(unix_zero)+int(hour_min[0])*3600+int(hour_min[1])*60
                else:
                    return -1
        else:
            return -1

if __name__ == '__main__':
    scanner = Scanner(args.dbip, args.dbport, args.dbusername, args.dbpassword, args.dbname, args.temp_path, args.unknown_path, args.timezone)
    scanner.start_detect('1080_02.png', '12313231331213', 1)
