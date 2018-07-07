import cv2
import numpy as np
import argparse
cap = cv2.VideoCapture(0)
from PIL import Image
import pytesseract
import datetime
import time
import matching as mt
import logging

Y1 = 585
Y2 = 908

X1 = 161
X2 = 380
X3 = 598

from skimage.measure import compare_ssim as ssim
import glob, os
import mysql;
import mysql.connector;

log = logging.getLogger(__name__)

class Scanner:
    def __init__(self, dbIp, dbPort, dbUser, dbPassword, dbName, tempPath):
        self.dbIp = dbIp
        self.dbPort = dbPort
        self.dbUser = dbUser
        self.dbPassword = dbPassword
        self.dbName = dbName
        self.tempPath = tempPath

        if not os.path.exists(self.tempPath):
            log.info('Temp directory created')
            os.makedirs(self.tempPath)

        if not os.path.exists('hash'):
            log.info('Hash directory created')
            os.makedirs('hash')

    def submitRaid(self, guid, pkm, lvl, start, end, type):
        log.error("Submitting raid")
        now = datetime.datetime.now()
        date1 = str(now.year) + "-0" + str(now.month) + "-" + str(now.day)
        date_plus_45 = now + datetime.timedelta(minutes = 45)
        today1 = date1 + " " + str(now.hour-2) + ":" + str(now.minute) + ":" + str(now.second)
        today2 = date1 + " " + str(now.hour-2) + ":" + str(now.minute) + ":" + str(now.second)
        fakeed = date1 + " " + str(date_plus_45.hour-2) + ":" + str(date_plus_45.minute) + ":" + str(date_plus_45.second)
        try:
            connection = mysql.connector.connect(host = self.dbIp, user = self.dbUser, passwd = self.dbPassword, db = self.dbName, port = self.dbPort)
        except:
            log.error("Error while connect to MySql Database")
            exit(0)

        cursor = connection.cursor()

        if type == 'EGG':
            query = " UPDATE raid SET level = %s, spawn=%s, start=%s, end=%s, pokemon_id = %s, cp = %s, move_1 = %s, move_2 = %s, last_scanned = %s WHERE gym_id = %s "
            data = (lvl, start, start, end, None, "999", "1", "1",  today1, guid)
            cursor.execute(query, data)
        else:
            query = " UPDATE raid SET level = %s, pokemon_id = %s, cp = %s, move_1 = %s, move_2 = %s, last_scanned = %s WHERE gym_id = %s "
            data = (lvl, pkm, "999", "1", "1",  today1, guid)
            cursor.execute(query, data)

        connection.commit()
        return 0


    def start_detect(self, filename, hash):
        log.error("Starting detection")
        if not os.path.isfile(filename):
            log.error("File does not exist")
            log.error(filename)
            return
        log.error("Starting analisys")
        now = datetime.datetime.now()
        date1 = str(now.year) + "-0" + str(now.month) + "-" + str(now.day)
        today1 = date1 + " " + str(now.hour) + ":" + str(now.minute) + ":" + str(now.second)
        today2 = date1 + " 00:01:00"

        img = cv2.imread(filename)
        img = cv2.resize(img, (750, 1334), interpolation = cv2.INTER_CUBIC)
        ###raid1
        raid1 = img[Y1-70:Y1+200,X1-80:X1+80]

        cv2.imwrite(self.tempPath + "/" + str(hash) + "_raid1.jpg", raid1)

        ###raid2
        raid2 = img[Y1-70:Y1+200, X2-80:X2+80]
        cv2.imwrite(self.tempPath + "/" + str(hash) + "_raid2.jpg", raid2)

        ###raid3
        raid3 = img[Y1-70:Y1+200, X3-80:X3+80]
        cv2.imwrite(self.tempPath + "/" + str(hash) + "_raid3.jpg", raid3)

        ###raid4
        raid4 = img[Y2-70:Y2+200, X1-80:X1+80]
        cv2.imwrite(self.tempPath + "/" + str(hash) + "_raid4.jpg", raid4)

        ###raid5
        raid5 = img[Y2-70:Y2+200, X2-80:X2+80]
        cv2.imwrite(self.tempPath + "/" + str(hash) + "_raid5.jpg", raid5)

        ###raid3
        raid6 = img[Y2-70:Y2+200, X3-80:X3+80]
        cv2.imwrite(self.tempPath + "/" + str(hash) + "_raid6.jpg", raid6)


        i = 1
        foundgym = None
        foundmon = None
        foundegg = None
        foundlvl = None

        while i < 7:
            gymfound = 0
            monfound = 0
            eggfound = 0
            lvlfound = 0
            image1 = cv2.imread(self.tempPath + "/" + str(hash) + "_raid" + str(i) +".jpg")
            raidpic = image1[0:165, 0:160]
            cv2.imwrite(self.tempPath + "/" + str(hash) + "_raidpic" + str(i) +".jpg", raidpic)

            image2 = cv2.imread(self.tempPath + "/" + str(hash) + "_raid" + str(i) +".jpg")
            raidtimer = image2[200:230, 0:297]
            raidtimer = cv2.resize(raidtimer, (0,0), fx=3, fy=3)
            cv2.imwrite(self.tempPath + "/" + str(hash) + "_raidtimer" + str(i) +".jpg", raidtimer)

            raidlevel = image2[235:265, 0:297]
            raidlevel = cv2.resize(raidlevel, (0,0), fx=3, fy=3)
            cv2.imwrite(self.tempPath + "/" + str(hash) + "_raidlevel" + str(i) +".jpg", raidlevel)

            #lower = np.array([86, 31, 4], dtype = "uint8")
        	#upper = np.array([220, 88, 50], dtype = "uint8")
            lower = np.array([86, 31, 4], dtype = "uint8")
            upper = np.array([220, 88, 50], dtype = "uint8")
            raidMonZoom = cv2.resize(image1, (0,0), fx=2, fy=2)
            mask = cv2.inRange(raidMonZoom, lower, upper)
            output = cv2.bitwise_and(raidMonZoom, raidMonZoom, mask = mask)
            cv2.imwrite(self.tempPath + "/" + str(hash) + "_raidboss" + str(i) +".jpg", output)
            monAsset = cv2.imread(self.tempPath + "/" + str(hash) + "_raidboss" + str(i) +".jpg",3)
            monAsset = cv2.inRange(monAsset,np.array([0,0,0]),np.array([15,15,15]))
            cv2.imwrite(self.tempPath + "/" + str(hash) + "_raidboss" + str(i) +".jpg", monAsset)

            emptyraid = image2[195:225, 0:160]
            cv2.imwrite(self.tempPath + "/" + str(hash) + "_emptyraid.png", raidtimer)
            rt = Image.open(self.tempPath + "/" + str(hash) + "_emptyraid.png")
            gray = rt.convert('L')
            bw = gray.point(lambda x: 0 if x<210 else 255, '1')
            bw.save(self.tempPath + "/" + str(hash) + "_cropped_emptyraid_bw.png")
            raidtext = pytesseract.image_to_string(Image.open(self.tempPath + "/" + str(hash) + "_cropped_emptyraid_bw.png"),config='-psm 7')


            raidtime = Image.open(self.tempPath + "/" + str(hash) + "_raidtimer" + str(i) +".jpg")
            gray = raidtime.convert('L')
            bw = gray.point(lambda x: 0 if x<185 else 255, '1')
            bw.save(self.tempPath + "/" + str(hash) + "_raidtimer" + str(i) +".jpg")
            timer = pytesseract.image_to_string(Image.open(self.tempPath + "/" + str(hash) + "_raidtimer" + str(i) +".jpg"),config='--psm=7').replace(' ', '').replace('~','').replace('o','0').replace('O','0').replace('-','')

            if len(raidtext) > 0:
                for file in glob.glob("mon_img/_egg_*.png"):
                    find_egg = mt.fort_image_matching(file, self.tempPath + "/" + str(hash) + "_raid" + str(i) +".jpg", True, 0.9)
                    if foundegg is None or find_egg > foundegg[0]:
    	    	    	foundegg = find_egg, file

                if not foundegg is None and foundegg[0]>0.9 and len(raidtext) > 0:
                    eggfound = 1

                if "R" not in timer:
                    raidstart = date1 + " 21:59"
                    raidend = date1 + " 22:59"
                    print timer
                    try:
                        aab = datetime.datetime(100,1,1,int(timer[:2]),int(timer[-2:]),00)
                        bba = aab - datetime.timedelta(minutes = 120) # days, seconds, then other fields.
                        raidstart = date1 + " " + str(bba.time())

                        a = datetime.datetime(100,1,1,int(timer[:2]),int(timer[-2:]),00)
                    #b = a - datetime.timedelta(0,4500) # days, seconds, then other fields.
                        b = bba + datetime.timedelta(minutes = 45)
                        raidend = date1 + " " + str(b.time())

                    except ValueError:

                         pass
                else:
                    raidstart = "-"

                print raidstart
                gymHash = self.imageHashExists(self.tempPath + "/" + str(hash) + "_raid" + str(i) +".jpg", True)
                if not gymHash:
                    for file in glob.glob("gym_img/*.jpg"):
                        find_gym = mt.fort_image_matching(self.tempPath + "/" + str(hash) + "_raid" + str(i) +".jpg", file, True, 0.7)
                        if foundgym is None or find_gym > foundgym[0]:
    	    	        	foundgym = find_gym, file

                        if not foundgym is None and foundgym[0]>0.7 and len(raidtext) > 0:
                            gymfound = 1
                            gymSplit = foundgym[1].split('_')
                            gymID = gymSplit[2]

                    if gymfound == 1:
                        self.imageHash('temp/' + str(hash) + '_raid' + str(i) +'.jpg', gymID, True)

                else:
                    gymfound = 1
                    gymID = gymHash


                for file in glob.glob("mon_img/_raidlevel_*.jpg"):
                    find_lvl = mt.fort_image_matching(file, self.tempPath + "/" + str(hash) + "_raidlevel" + str(i) +".jpg", False, 0.5)
                    if foundlvl is None or find_lvl > foundlvl[0]:
    	    	    	foundlvl = find_lvl, file

                if not foundlvl is None and foundlvl[0]>0.5 and len(raidtext) > 0:
                    lvlfound = 1

                if eggfound == 0:
                    monHash = self.imageHashExists(self.tempPath + "/" + str(hash) + "_raidboss" + str(i) +".jpg", False)
                    if not monHash:
                        for file in glob.glob("mon_img/_mon_*.png"):
                            find_mon = mt.fort_image_matching(file, self.tempPath + "/" + str(hash) + "_raidboss" + str(i) +".jpg", False, 0.7)
                            if foundmon is None or find_mon > foundmon[0]:
                                foundmon = find_mon, file

                            if not foundmon is None and foundmon[0]>0.7 and len(raidtext) > 0:
                                monfound = 1
                                monSplit = foundmon[1].split('_')
                                monID = monSplit[3]

                        if monfound == 1:
                            self.imageHash('temp/' + str(hash) + '_raidboss' + str(i) +'.jpg', monID, False)
                    else:
                        monfound = 1
                        monID = monHash


                if gymfound == 1 and (monfound == 1 or eggfound == 1):

                    lvlSplit = foundlvl[1].split('_')
                    lvl = lvlSplit[3]


                    if monfound == 1:
                        logtext = 'Mon - ID: ' + str(monID)

                        self.submitRaid(str(gymID), monID, lvl, '-', '-', 'MON')

                    if eggfound == 1:
                        eggSplit = foundegg[1].split('_')
                        eggID = eggSplit[3]
                        logtext = 'Egg - ID: ' + str(eggID)

                        self.submitRaid(str(gymID), '0', lvl, raidstart, raidend, 'EGG')

                    log.info('Raid ' + str(i) + ' | Gym-ID: ' + str(gymID) + ' | ' + logtext + ' | Level: ' + lvl)

                if gymfound == 1 and (monfound == 0 and eggfound == 0):

                    #gymSplit = foundgym[1].split('_')
                    #gymID = gymSplit[2]
                    lvlSplit = foundlvl[1].split('_')
                    lvl = lvlSplit[3]

                    logtext = ' Mon or Egg: unknows '

                    log.info('Raid ' + str(i) + ' | Gym-ID: ' + str(gymID) + ' | ' + logtext + ' | Level: ' + lvl)

                if gymfound == 0 and (monfound == 1 or eggfound == 1):
                    gymID = 'unknow'
                    lvlSplit = foundlvl[1].split('_')
                    lvl = lvlSplit[3]

                    if monfound == 1:
                        logtext = 'Mon - ID: ' + str(monID)

                    if eggfound == 1:
                        eggSplit = foundegg[1].split('_')
                        eggID = eggSplit[3]
                        logtext = 'Egg - ID: ' + str(eggID)

                    log.info('Raid ' + str(i) + ' | Gym-ID: ' + str(gymID) + ' | ' + logtext + ' | Level: ' + lvl)

                if gymfound == 0 and (monfound == 0 and eggfound == 0):

                    lvlSplit = foundlvl[1].split('_')
                    lvl = lvlSplit[3]
                    gymID = 'uknown'
                    logtext = ' unknown Mon or Egg '

                    log.info('Raid ' + str(i) + ' | Gym-ID: ' + str(gymID) + ' | ' + logtext + ' | Level: ' + lvl)

                foundmon = None
                foundgym = None
                foundegg = None
                foundlvl = None
            else:
                if i == 1:
                    log.error('No active Raids ' + str(i) + ' | empty')
                    break
                else:
                    log.error('Raid ' + str(i) + ' | empty')

    ##############################################
            if gymfound == 0 and len(raidtext) > 0:
                unknowngymfound = 0
                for file in glob.glob("unknown/gym_*.jpg"):
                            foundunknowngym = mt.fort_image_matching(self.tempPath + "/" + str(hash) + "_raidpic" + str(i) +".jpg", file, True, 0.8)
                            if foundgym is None or foundunknowngym > foundgym[0]:
                	    		foundgym = foundunknowngym, file

                            if not foundgym is None and foundgym[0]>0.8:
                                unknowngymfound = 1
                                foundgym = None

                if unknowngymfound == 0:
                    name22 = time.time()
                    cv2.imwrite("unknown/gym_" + str(name22) +".jpg", raidpic)

            if monfound == 0 and len(raidtext) > 0 and eggfound == 0:
                unknownmonfound = 0
                for file in glob.glob("unknown/mon_*.jpg"):

                            foundunknownmon = mt.fort_image_matching(self.tempPath + "/" + str(hash) + "_raidboss" + str(i) +".jpg", file, False, 0.8)
                            if foundmon is None or foundunknownmon > foundmon[0]:
                	    		foundmon = foundunknownmon, file


                            if not foundmon is None and foundmon[0]>0.8:
                                unknownmonfound = 1
                                foundmon = None

                if unknownmonfound == 0:
                    name22 = time.time()
                    cv2.imwrite("unknown/mon_" + str(name22) +".jpg", monAsset)

            gymfound = None
            foundmon = None
            foundgym = None
            raidtext = None
            foundegg = None
            eggfound = None
            lvlfound = None
            i = i + 1

        for file in glob.glob(self.tempPath + "/" + str(hash) + "_*raid*.jpg"):
            os.remove(file)
        os.remove(self.tempPath + "/" + str(hash) + "_cropped_emptyraid_bw.png")
        os.remove(self.tempPath + "/" + str(hash) + "_emptyraid.png")


    def imageHashExists(self, image, zoom, hashSize=8):
        image2 = cv2.imread(image,3)
        image2 = cv2.cvtColor(image2, cv2.COLOR_BGR2GRAY)
        if zoom:
            image2 = cv2.resize(image2,None,fx=2, fy=2, interpolation = cv2.INTER_NEAREST)
            crop = image2[int(80):int(200),int(80):int(110)]
        else:
            crop = image2
        resized = cv2.resize(crop, (hashSize + 1, hashSize))
        diff = resized[:, 1:] > resized[:, :-1]
        imageHash = sum([2 ** i for (i, v) in enumerate(diff.flatten()) if v])
        for file in glob.glob('hash/*' + str(imageHash) + '_*'):
                    Split = file.split('_')
                    return Split[2]

        return False

    def imageHash(self, image, id, zoom, hashSize=8):
        image2 = cv2.imread(image, 3)
        image2 = cv2.cvtColor(image2, cv2.COLOR_BGR2GRAY)
        if zoom:
            image2 = cv2.resize(image2,None,fx=2, fy=2, interpolation = cv2.INTER_NEAREST)
            crop = image2[int(80):int(200),int(80):int(110)]
        else:
            crop = image2

        resized = cv2.resize(crop, (hashSize + 1, hashSize))
        diff = resized[:, 1:] > resized[:, :-1]
        imageHash = sum([2 ** i for (i, v) in enumerate(diff.flatten()) if v])
        file = open('hash/_' + str(imageHash) + '_' + str(id) + '_','w')
        file.write(id)
        file.close()
