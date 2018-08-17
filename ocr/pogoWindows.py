# -*- coding: utf-8 -*-

import cv2
import numpy as np
import logging
from PIL import Image
#import pytesseract
from pytesseract import image_to_string
from resolutionCalculator import *
import os
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

    def __checkPostLoginOkButton(self, filename, hash, type, ratio):
        if not os.path.isfile(filename):
            return False
        log.debug('checkPostLoginOkButton: Checking for post-login ok button of type %s...' % type)
        pos = None
        if type == 'post_login_ok_driving':
            pos = self.resolutionCalculator.getPostLoginOkDrivingClick()
        else:
            pos = self.resolutionCalculator.getPostLoginOkPrivatePropertyClick()

        if not self.__lookForButton(filename, 2.20, pos.y):
            log.debug('checkPostLoginOkButton: Could not find OK button')
            return False
        else:
            log.debug('checkPostLoginOkButton: Found post login OK button - closing ...')
            
            
            self.screenWrapper.click(pos.x, pos.y)
            return True

    def checkPostLoginOkButton(self, filename, hash):
        log.debug('checkPostLoginOkButton: Starting check')
        return (self.__checkPostLoginOkButton(filename, hash, 'post_login_ok_driving', 26)
            or self.__checkPostLoginOkButton(filename, hash, 'post_login_ok_private_property', 17))

    def __readCircleCount(self,filename,hash,ratio, xcord = False):
        log.debug("__readCircleCount: Reading circles")

        screenshotRead = cv2.imread(filename)
        height, width, _ = screenshotRead.shape
        log.debug("__readCircleCount: Determined screenshot scale: " + str(height) + " x " + str(width))
        gray = cv2.cvtColor(screenshotRead, cv2.COLOR_BGR2GRAY)
        # detect circles in the image

        radMin = int((width / float(ratio) - 3) / 2)
        radMax = int((width / float(ratio) + 3) / 2)
        log.debug("__readCircleCount: Detect radius of circle: Min " + str(radMin) + " Max " + str(radMax))
        circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT,1,width / 8,param1=100,param2=15,minRadius=radMin,maxRadius=radMax)
        circle = 0
        # ensure at least some circles were found
        if circles is not None:
            # convert the (x, y) coordinates and radius of the circles to integers
            circles = np.round(circles[0, :]).astype("int")
            # loop over the (x, y) coordinates and radius of the circles
            for (x, y, r) in circles:
                if not xcord:
                    circle += 1
                else:
                    if x >= (width/2)-100 and x <= (width/2)+100 and y>=(height-(height/3)):
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


    def __lookForButton(self, filename, ratio, minmiddledist = False, max = False):
        log.debug("lookForButton: Reading lines")
        disToMiddleMin = None
        screenshotRead = cv2.imread(filename)
        gray = cv2.cvtColor(screenshotRead,cv2.COLOR_BGR2GRAY)
        height, width, _ = screenshotRead.shape
        log.debug("lookForButton: Determined screenshot scale: " + str(height) + " x " + str(width))
        gray = cv2.GaussianBlur(gray,(5, 5), 0)
        edges = cv2.Canny(gray,100,200,apertureSize = 3)
        maxLineLength = width / ratio + 15
        log.debug("lookForButton: MaxLineLength:" + str(maxLineLength))
        minLineLength = width / ratio - 25
        log.debug("lookForButton: MinLineLength:" + str(minLineLength))
        maxLineGap = 50
        lineCount = 0
        lines = []
        lines = cv2.HoughLinesP(edges,1,np.pi/180,160,maxLineGap, minLineLength)
        if lines is None:
            return False
            
        for line in lines:
            for x1,y1,x2,y2 in line:
                if y1 == y2 and (x2-x1<=maxLineLength) and (x2-x1>=minLineLength) and y1 > height/2:
                    lineCount += 1
                    disToMiddle = y1
                    
                    if not max:
                        if disToMiddleMin is None or disToMiddle < disToMiddleMin:
                	        disToMiddleMin = disToMiddle
                    else:
                        if disToMiddleMin is None or disToMiddle > disToMiddleMin:
                	        disToMiddleMin = disToMiddle
                    
                        
                    log.debug("lookForButton: Found Buttonline Nr. " + str(lineCount) + " - Line lenght: " + str(x2-x1) + "px Coords - X: " + str(x1) + " " + str(x2) + " Y: " + str(y1) + " " + str(y2))

        if lineCount >= 1:
            log.debug("lookForButton: disToMiddleMin: " + str(disToMiddleMin))
            log.debug("lookForButton: minmiddledist: " + str(minmiddledist))
            if minmiddledist:
                log.debug("lookForButton: Check Y-cord of button")
                if disToMiddleMin-((height/25)-5) < minmiddledist and disToMiddleMin+((height/25)+5) > minmiddledist:
                    log.debug("lookForButton: Button found")
                    return True
                else:
                    log.debug("lookForButton: Button not found")
                    return False
            else:
                log.debug("lookForButton: Button found")
                return True

        log.debug("lookForButton: Button not found")
        return False

    def __checkRaidLine(self, filename, hash, leftSide = False):
        log.debug("__checkRaidLine: Reading lines")
        if leftSide:
            log.debug("__checkRaidLine: Check nearby open " )
        screenshotRead = cv2.imread(filename)
        height, width, _ = screenshotRead.shape
        screenshotRead = screenshotRead[int(height/2)-int(height/3):int(height/2)+int(height/3),int(0):int(width)]
        gray = cv2.cvtColor(screenshotRead,cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray,(5, 5), 0)
        log.debug("__checkRaidLine: Determined screenshot scale: " + str(height) + " x " + str(width))
        edges = cv2.Canny(gray,50,150,apertureSize = 3)
        maxLineLength = width / 3.30 + 30
        log.debug("__checkRaidLine: MaxLineLength:" + str(maxLineLength))
        minLineLength = width / 3.30 - 30
        log.debug("__checkRaidLine: MinLineLength:" + str(minLineLength))
        maxLineGap = 50
        lines = cv2.HoughLinesP(edges,1,np.pi/180,100,minLineLength,maxLineGap)
        if lines is None:
            return False
        for line in lines:
            for x1,y1,x2,y2 in line:
                if not leftSide:
                    if y1 == y2 and (x2-x1<=maxLineLength) and (x2-x1>=minLineLength) and x1 > width/2 and y1<(height/2):
                        log.debug("__checkRaidLine: Raid-tab is active - Line lenght: " + str(x2-x1) + "px Coords - X: " + str(x1) + " " + str(x2) + " Y: " + str(y1) + " " + str(y2))
                        return True
                    #else:
                        #log.debug("__checkRaidLine: Raid-tab is not active - Line lenght: " + str(x2-x1) + "px Coords - X: " + str(x1) + " " + str(x2) + " Y: " + str(y1) + " " + str(y2))
                        #return False
                else:
                    if y1 == y2 and (x2-x1<=maxLineLength) and (x2-x1>=minLineLength) and x1 < width/2 and y1<(height/2):
                        log.debug("__checkRaidLine: Nearby is active - but not Raid-tab")
                        return True
                    #else:
                        #log.debug("__checkRaidLine: Nearby not active - but maybe Raid-tab")
                        #return False
        log.debug("__checkRaidLine: Not active")
        return False

    def readAmountOfRaidsCircle(self, filename, hash):
        if not os.path.isfile(filename):
            return None

        log.debug("readAmountOfRaidsCircle: Cropping circle")
        
        image = cv2.imread(filename)
        height, width, _ = image.shape
        image = image[int(height/2-(height/3)):int(height/2+(height/3)),0:int(width)]
        cv2.imwrite(os.path.join(self.tempDirPath, str(hash) + '_AmountOfRaids.jpg'), image)

        if self.__readCircleCount(os.path.join(self.tempDirPath, str(hash) + '_AmountOfRaids.jpg'), hash, 18.95) > 0:
            log.info("readAmountOfRaidsCircle: Raidcircle found, assuming raids nearby")
            os.remove(os.path.join(self.tempDirPath, str(hash) + '_AmountOfRaids.jpg'))
            return True
        else:
            log.info("readAmountOfRaidsCircle: No raidcircle found, assuming no raids nearby")
            os.remove(os.path.join(self.tempDirPath, str(hash) + '_AmountOfRaids.jpg'))
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
        
        if self.__checkRaidLine(filename, hash):
            log.debug('checkRaidscreen: RAID-tab found')
            return True
        if self.__checkRaidLine(filename, hash, True):
                #RAID Tab not active
            log.debug('checkRaidscreen: RAID-tab not activated')
            #pos = self.resolutionCalculator.getNearbyRaidTabClick()
            #self.screenWrapper.click(pos.x, pos.y)
            #time.sleep(.5)
            #log.debug('checkRaidscreen: RAID-tab clicked')
            return False

        log.debug('checkRaidscreen: nearby not found')
            #log.warning('checkRaidscreen: Could not locate RAID-tab')
        return False

    def checkNearby(self, filename, hash):
        if self.__checkRaidLine(filename, hash):
            log.info('Nearby already open')
            return True
            
        if self.__checkRaidLine(filename, hash, True):
            log.info('Raidscreen not running but nearby open')
            posRaids = self.resolutionCalculator.getNearbyRaidTabClick()
            self.screenWrapper.click(posRaids.x, posRaids.y)
            time.sleep(.5)
            return False
        
        log.info('Raidscreen not running...')
        posNearby = self.resolutionCalculator.getNearbyClick()
        self.screenWrapper.click(posNearby.x, posNearby.y)
        time.sleep(.5)
        posRaids = self.resolutionCalculator.getNearbyRaidTabClick()
        self.screenWrapper.click(posRaids.x, posRaids.y)
        time.sleep(.5)
        return False


    def checkGameQuitPopup(self, filename, hash):
        if not os.path.isfile(filename):
            return False

        log.debug('checkGameQuitPopup: Checking for quit-game popup ...')
        pos = None
        pos = self.resolutionCalculator.getquitGameClick()
        bounds = self.resolutionCalculator.getQuitGamePopupBounds()
        if not self.__lookForButton(filename, 2.20, bounds.top):
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
        bounds = self.resolutionCalculator.getSpeedwarningBounds()

        if not self.__lookForButton(filename, 1.60, bounds.bottom, True):
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

    def __checkClosePresent(self, filename, hash, windowsToCheck, radiusratio=12, Xcord=True):
        if not os.path.isfile(filename):
            log.warning("__checkClosePresent: %s does not exist" % str(filename))
            return False
              
        image = cv2.imread(filename)
        height, width, _ = image.shape
        image = image[int(height)-int(height/4.5):int(height),int(width)/2-int(width)/8:int(width)/2+int(width)/8]
        cv2.imwrite(os.path.join(self.tempDirPath, str(hash) + '_exitcircle.jpg'), image)
             
        if self.__readCircleCount(os.path.join(self.tempDirPath, str(hash) + '_exitcircle.jpg'), hash, float(radiusratio), Xcord) > 0:
            return True

    def isNewsQuestCloseButtonPresent(self, filename, hash):
        return self.__checkClosePresent(filename, hash, 'news_or_quest')

    #check for other close buttons (menu, raidtab etc)
    def isOtherCloseButtonPresent(self, filename, hash):
        return self.__checkClosePresent(filename, hash, 'menu_or_raid')

    #checks for X button on any screen... could kill raidscreen, handle properly
    def checkCloseExceptNearbyButton(self, filename, hash):
        if (not os.path.isfile(filename) 
            or self.__checkRaidLine(filename, hash)):
            #file not found or raid tab present
            log.debug("checkCloseExceptNearbyButton: Not checking for close button (X). Input wrong OR nearby window open")
            return False
            
        log.debug("checkCloseExceptNearbyButton: Checking for close button (X). Input wrong OR nearby window open")   

        if (self.isOtherCloseButtonPresent(filename, hash)):
            log.debug("Found close button (X). Closing the window")
            self.screenWrapper.backButton()
            return True
        if (self.__checkClosePresent(filename, hash, 'gym', 14, False)):
            log.debug("Found close button (X). Closing the window")
            self.screenWrapper.backButton()
            return True
        if (self.__checkClosePresent(filename, hash, 'gym', 13, False)):
            log.debug("Found close button (X). Closing the window")
            self.screenWrapper.backButton()
            return True
        else:
            log.debug("Could not find close button (X).")
            return False
