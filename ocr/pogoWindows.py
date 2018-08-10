# -*- coding: utf-8 -*-

import cv2
import numpy as np
import logging
from PIL import Image
#import pytesseract
from pytesseract import image_to_string
from resolutionCalculator import *

import os.path
import sys
sys.path.insert(0, '../')
from screenWrapper import ScreenWrapper
import collections
import re
import time

import sys
reload(sys)
sys.setdefaultencoding('utf8')

Coordinate = collections.namedtuple("Coordinate", ['x', 'y'])
Bounds = collections.namedtuple("Bounds", ['top', 'bottom', 'left', 'right'])

log = logging.getLogger(__name__)



class PogoWindows:
    def __init__(self, screenWrapper, width, height, tempDirPath):
        self.screenWrapper = screenWrapper
        self.resolutionCalculator = ResolutionCalc(width, height)
        if not os.path.exists(tempDirPath):
            os.makedirs(tempDirPath)
            log.info('PogoWindows: Temp directory created')
        self.tempDirPath = tempDirPath
        self.width = width
        self.height = height

    def __mostPresentColour(self, filename, maxColours):
        img = Image.open(filename)
        colors = img.getcolors(maxColours) #put a higher value if there are many colors in your image
        max_occurence, most_present = 0, 0
        try:
            for c in colors:
                if c[0] > max_occurence:
                    (max_occurence, most_present) = c
            return most_present
        except TypeError:
            return None

    def __checkPostLoginOkButton(self, filename, hash, type):
        if not os.path.isfile(filename):
            return False
        log.debug('checkPostLoginOkButton: Checking for post-login ok button of type %s...' % type)

        if not self.__lookForButton(filename, 2.20):
            log.debug('checkPostLoginOkButton: Could not find OK button')
            return False
        else:
            log.debug('checkPostLoginOkButton: Found post login OK button - closing ...')
            pos = None
            if type == 'post_login_ok_driving':
                pos = self.resolutionCalculator.getPostLoginOkDrivingClick()
            else:
                pos = self.resolutionCalculator.getPostLoginOkPrivatePropertyClick()
            self.screenWrapper.click(pos.x, pos.y)
            return True

    def checkPostLoginOkButton(self, filename, hash):
        log.debug('checkPostLoginOkButton: Starting check')
        return (self.__checkPostLoginOkButton(filename, hash, 'post_login_ok_driving')
            or self.__checkPostLoginOkButton(filename, hash, 'post_login_ok_private_property'))

    def __readCircleCount(self,filename,hash,ratio):
        log.debug("__readCircleCount: Reading circles")

        screenshotRead = cv2.imread(filename)
        height, width, _ = screenshotRead.shape
        log.debug("__readCircleCount: Determined screenshot scale: " + str(height) + " x " + str(width))
        gray = cv2.cvtColor(screenshotRead, cv2.COLOR_BGR2GRAY)
        # detect circles in the image

        radMin = int((width / ratio - 3) / 2)
        radMax = int((width / ratio + 3) / 2)
        log.debug("__readCircleCount: Detect radius of circle: Min " + str(radMin) + " Max " + str(radMax))
        circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT,1,width / 8,param1=100,param2=15,minRadius=radMin,maxRadius=radMax)
        circle = 0
        # ensure at least some circles were found
        if circles is not None:
            # convert the (x, y) coordinates and radius of the circles to integers
            circles = np.round(circles[0, :]).astype("int")
            # loop over the (x, y) coordinates and radius of the circles
            for (x, y, r) in circles:
                circle += 1

            log.debug("__readCircleCount: Determined screenshot to have " + str(circle) + " Circle.")
            return circle
        else:
            log.debug("__readCircleCount: Determined screenshot to have 0 Circle")
            return -1



    def readRaidCircles(self, filename, hash):
        log.debug("readCircles: Reading circles")
        if not self.readAmountOfRaidsCircle(filename, hash):
            #no raidcount (orange circle) present...
            return 0

        circle = self.__readCircleCount(filename, hash, 4.7)

        if circle > 6:
            circle = 6

        if circle > 0:
            log.debug("readCircles: Determined screenshot to have " + str(circle) + " Circle.")
            return circle

        log.debug("readCircles: Determined screenshot to not contain raidcircles, but a raidcount!")
        return -1


    def __lookForButton(self, filename, ratio):
        log.debug("lookForButton: Reading lines")
        screenshotRead = cv2.imread(filename)
        gray = cv2.cvtColor(screenshotRead,cv2.COLOR_BGR2GRAY)
        height, width, _ = screenshotRead.shape
        log.debug("lookForButton: Determined screenshot scale: " + str(height) + " x " + str(width))
        edges = cv2.Canny(gray,100,200,apertureSize = 3)
        maxLineLength = width / ratio + 10 #0
        log.debug("lookForButton: MaxLineLength:" + str(maxLineLength))
        minLineLength = width / ratio - 30 #-10
        log.debug("lookForButton: MinLineLength:" + str(minLineLength))
        maxLineGap = 10
        lineCount = 0
        lines = cv2.HoughLinesP(edges,1,np.pi/180,100,minLineLength,maxLineGap)
        for line in lines:
            for x1,y1,x2,y2 in line:
                if y1 == y2 and (x2-x1<=maxLineLength) and (x2-x1>=minLineLength) and y1 > height/2:
                    lineCount += 1
                    log.debug("lookForButton: Found Buttonline Nr. " + str(lineCount) + " - Line lenght: " + str(x2-x1) + "px Coords - X: " + str(x1) + " " + str(x2) + " Y: " + str(y1) + " " + str(y2))

        if lineCount >= 1:
            log.debug("lookForButton: Button found")
            return True

        log.debug("lookForButton: Button not found")
        return False

    def __checkRaidLine(self, filename, hash):
        log.debug("checkRaidLine: Reading lines")
        screenshotRead = cv2.imread(filename)
        gray = cv2.cvtColor(screenshotRead,cv2.COLOR_BGR2GRAY)
        height, width, _ = screenshotRead.shape
        log.debug("__checkRaidLine: Determined screenshot scale: " + str(height) + " x " + str(width))
        edges = cv2.Canny(gray,100,200,apertureSize = 3)
        maxLineLength = width / 3.30
        log.debug("__checkRaidLine: MaxLineLength:" + str(maxLineLength))
        minLineLength = width / 3.30 - 10
        log.debug("__checkRaidLine: MinLineLength:" + str(minLineLength))
        maxLineGap = 10
        lines = cv2.HoughLinesP(edges,1,np.pi/180,100,minLineLength,maxLineGap)
        for line in lines:
            for x1,y1,x2,y2 in line:
                if y1 == y2 and (x2-x1<=maxLineLength) and (x2-x1>=minLineLength) and x1 > width/2:
                    log.debug("__checkRaidLine: Raid-tab is active - Line lenght: " + str(x2-x1) + "px Coords - X: " + str(x1) + " " + str(x2) + " Y: " + str(y1) + " " + str(y2))
                    return True
        log.debug("__checkRaidLine: Raid-tab is not active")
        return False

    def readAmountOfRaidsCircle(self, filename, hash):
        if not os.path.isfile(filename):
            return None

        log.debug("readAmountOfRaidsCircle: Cropping circle")
        
        image = cv2.imread(filename)
        height, width, _ = image.shape
        image = image[int(height/2-(height/3)):int(height/2+(height/3)),0:int(width)]
        cv2.imwrite(self.tempDirPath + "/" + str(hash) + "_AmountOfRaids.jpg", image)

        if self.__readCircleCount(self.tempDirPath + "/" + str(hash) + "_AmountOfRaids.jpg", hash, 18.95) > 0:
            log.info("readAmountOfRaidsCircle: Raidcircle found, assuming raids nearby")
            os.remove(self.tempDirPath + "/" + str(hash) + "_AmountOfRaids.jpg")
            return True
        else:
            log.info("readAmountOfRaidsCircle: No raidcircle found, assuming no raids nearby")
            os.remove(self.tempDirPath + "/" + str(hash) + "_AmountOfRaids.jpg")
            return False


    def checkPostLoginNewsMessage(self, filename, hash):
        if not os.path.isfile(filename):
            return False


        log.debug('checkPostLoginNewsMessage: Checking for small news popup ...')

        if not self.__lookForButton(filename, 3.01):
            log.debug('checkPostLoginNewsMessage: no popup found')
            return False
        else:
            log.debug('checkPostLoginNewsMessage: found popup - closing ...')
            self.screenWrapper.backButton()
            return True

    def __checkRaidTabOnScreen(self, filename, hash):
        if not os.path.isfile(filename):
            return False

        log.debug('__checkRaidTabOnScreen: Checking for raidscreen ...')
        col = cv2.imread(filename)
        bounds = self.resolutionCalculator.getNearbyRaidTabBounds()
        log.debug("__checkRaidTabOnScreen: Bounds %s" % str(bounds))
        raidtimer = col[bounds.top:bounds.bottom, bounds.left:bounds.right]
        cv2.imwrite(self.tempDirPath + "/" + str(hash) + "_message.jpg", raidtimer)
        col = Image.open(self.tempDirPath + "/" + str(hash) + "_message.jpg")
        gray = col.convert('L')
        bw = gray.point(lambda x: 0 if x<210 else 255, '1')
        bw.save(self.tempDirPath + "/" + str(hash) + "_cropped_message_bw.jpg")

        text = image_to_string(Image.open(self.tempDirPath + "/" + str(hash) + "_cropped_message_bw.jpg"), config='-c tessedit_char_whitelist=RAID -psm 7')
        log.debug("__checkRaidTabOnScreen: Check for raidtab present resulted in text: %s" % text)

        os.remove('temp/' + str(hash) + '_cropped_message_bw.jpg')
        os.remove('temp/' + str(hash) + '_message.jpg')
        if 'RAID' in text:
            log.debug("__checkRaidTabOnScreen: Found raidtab")
            return True
        else:
            log.debug("__checkRaidTabOnScreen: Could not find raidtab")
            return False

    #assumes we are on the general view of the game
    def checkRaidscreen(self, filename, hash):
        log.debug("checkRaidscreen: Checking if RAID is present (nearby tab)")
        if self.__checkRaidTabOnScreen(filename, hash):
            #RAID Tab visible
            log.debug('checkRaidscreen: RAID-tab found')
            if not self.__checkRaidLine(filename, hash):
                #RAID Tab not active
                log.debug('checkRaidscreen: RAID-tab not activated')
                pos = self.resolutionCalculator.getNearbyRaidTabClick()
                self.screenWrapper.click(pos.x, pos.y)
                time.sleep(1)
                log.debug('checkRaidscreen: RAID-tab clicked')
                return True
            return True
        else:
            log.warning('checkRaidscreen: Could not locate RAID-tab')
            return False

    def checkNearby(self, filename, hash):
        if not self.__checkRaidTabOnScreen(filename, hash):
            #RAID Tab not visible => not on Nearby screen
            log.info('Raidscreen not running...')
            posNearby = self.resolutionCalculator.getNearbyClick()
            self.screenWrapper.click(posNearby.x, posNearby.y)
            time.sleep(1)
            posRaids = self.resolutionCalculator.getNearbyRaidTabClick()
            self.screenWrapper.click(posRaids.x, posRaids.y)
            return False
        else:
            log.info('Nearby already open')
            return True

    def checkGameQuitPopup(self, filename, hash):
        if not os.path.isfile(filename):
            return False

        log.debug('checkGameQuitPopup: Checking for quit-game popup ...')

        if not self.__lookForButton(filename, 2.20):
            log.debug('checkGameQuitPopup: Could not find quit popup')
            return False
        else:
            log.info('checkGameQuitPopup: Found quit popup - aborting quit ...')
            self.screenWrapper.backButton()
            return True

    def checkSpeedwarning(self, filename, hash):
        if not os.path.isfile(filename):
            return False

        log.debug('checkSpeedwarning: Checking for speed-warning ...')

        if not self.__lookForButton(filename, 1.60):
            log.debug('checkSpeedwarning: No speedmessage found')
            return False
        else:
            log.debug('checkSpeedwarning: Found Speedmessage - closing ...')
            posPassenger = self.resolutionCalculator.getSpeedwarningClick()
            log.debug("checkSpeedwarning: Clicking %s" % str(posPassenger))
            self.screenWrapper.click(posPassenger.x, posPassenger.y)
            return True

    def checkWeatherWarning(self, filename, hash):
        if not os.path.isfile(filename):
            return False

        log.debug('checkWeatherwarning: Checking for weatherwarning ...')

        if not self.__lookForButton(filename, 1.05):
            log.debug('checkWeatherwarning: No weatherwarning found')
            return False
        else:
            log.debug('checkWeatherwarning: Found weather warning - closing ...')
            posPassenger = self.resolutionCalculator.getWeatherWarningFirstClick()
            log.debug("checkWeatherwarning: Clicking %s" % str(posPassenger))
            self.screenWrapper.click(posPassenger.x, posPassenger.y)
            time.sleep(1)
            log.debug('checkWeatherwarning: Also closing the weather info ...')
            posPassenger = self.resolutionCalculator.getWeatherWarningSecondClick()
            log.debug("checkWeatherwarning: Clicking %s" % str(posPassenger))
            self.screenWrapper.click(posPassenger.x, posPassenger.y)
            return True

    def __checkClosePresent(self, filename, hash, windowsToCheck):
        if not os.path.isfile(filename):
            log.warning("__checkClosePresent: %s does not exist" % str(filename))
            return False

        bounds = None
        col = cv2.imread(filename)
        if (windowsToCheck == 'news_or_quest'):
            log.debug('__checkClosePresent: Checking for news or quest close button')
            bounds = self.resolutionCalculator.getNewsQuestCloseButtonBounds()
        else:
            log.debug('__checkClosePresent: Checking for menu or raids close button')
            bounds = self.resolutionCalculator.getMenuRaidsCloseButtonBounds()

        log.debug('__checkClosePresent: checking bounds %s' % str(bounds))
        closeButton = col[bounds.top:bounds.bottom, bounds.left:bounds.right]
        tempPath = self.tempDirPath + "/" + str(hash) + "_xbutton.jpg"
        log.debug("TempPath: %s" % tempPath)
        cv2.imwrite(tempPath, closeButton)

        im = Image.open(tempPath)
        width, height = im.size

        mostPresentColour = self.__mostPresentColour(tempPath, width * height)
        log.debug("__checkClosePresent: found most present colour %s" % str(mostPresentColour))
        os.remove(self.tempDirPath + "/" + str(hash) + "_xbutton.jpg")
        return (mostPresentColour == (28, 135, 150)
            or mostPresentColour == (236, 252, 235)
            or mostPresentColour == (42, 119, 125)
            or mostPresentColour == (29, 134, 153))

    def isNewsQuestCloseButtonPresent(self, filename, hash):
        return self.__checkClosePresent(filename, hash, 'news_or_quest')

    #check for other close buttons (menu, raidtab etc)
    def isOtherCloseButtonPresent(self, filename, hash):
        return self.__checkClosePresent(filename, hash, 'menu_or_raid')

    #checks for X button on any screen... could kill raidscreen, handle properly
    def checkCloseExceptNearbyButton(self, filename, hash):
        if (not os.path.isfile(filename)
            or self.__checkRaidTabOnScreen(filename, hash)):
            #file not found or raid tab present
            log.debug("Not checking for close button (X). Input wrong OR nearby window open")
            return False

        #we are not on the nearby window, check for X
        #self.isNewsQuestCloseButtonPresent(filename, hash)
            #or
        if (self.isOtherCloseButtonPresent(filename, hash)):
            #X button found and not on nearby (we checked that earlier)
            log.debug("Found close button (X). Closing the window")
            self.screenWrapper.backButton()
            return True
        else:
            log.debug("Could not find close button (X).")
            return False
