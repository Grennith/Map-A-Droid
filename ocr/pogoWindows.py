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
from vnc.vncWrapper import VncWrapper
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
    def __init__(self, vncIp, vncScreen, vncPort, vncPassword, width, height, tempDirPath):
        self.vncWrapper = VncWrapper(str(vncIp), vncScreen, vncPort, vncPassword)
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
        col = cv2.imread(filename)
        bounds = None
        if type == 'post_login_ok_driving':
            bounds = self.resolutionCalculator.getPostLoginOkDrivingBounds()
        else:
            bounds = self.resolutionCalculator.getPostLoginOkPrivatePropertyBounds()

        okFont = col[bounds.top:bounds.bottom, bounds.left:bounds.right]
        log.debug('checkPostLoginOkButton: bounds of okFont: %s' % str(bounds))

        tempPathColoured = self.tempDirPath + "/" + str(hash) + "_login.png"
        cv2.imwrite(tempPathColoured, okFont)

        col = Image.open(tempPathColoured)
        width, height = col.size

        #check for the colour of the button that says "show all"
        mostPresentColour = self.__mostPresentColour(tempPathColoured, width * height)
        log.debug('checkSpeedwarning: most present colour is %s' % str(mostPresentColour))
        #just gonna check the most occuring colours on that button...
        if (mostPresentColour != (144, 217, 152)
            and mostPresentColour != (145, 217, 152)
            and mostPresentColour != (146, 217, 152)
            and mostPresentColour != (152, 218, 151)
            and mostPresentColour != (153, 218, 151)
            and mostPresentColour != (151, 218, 151)
            and mostPresentColour != (77, 209, 163)
            and mostPresentColour != (255, 255, 255)):
            return False

        gray = col.convert('L')
        bw = gray.point(lambda x: 0 if x<210 else 255, '1')
        bw.save(self.tempDirPath + "/" + str(hash) + "_cropped_login_bw.png")
        text = image_to_string(Image.open(self.tempDirPath + "/" + str(hash) + "_cropped_login_bw.png"),config='--oem 3 --psm 7')

        #cleanup
        os.remove(self.tempDirPath + "/" + str(hash) + "_login.png")
        os.remove(self.tempDirPath + "/" + str(hash) + "_cropped_login_bw.png")

        log.debug("checkPostLoginOkButton: Checking for post-login OK button found: %s" % text)
        #if 'O. K.' in text:
        if re.match(r'.*[oO0][.\n\s]*[kK].*', text):
            log.debug('checkPostLoginOkButton: Found post login OK button - closing ...')
            pos = None
            if type == 'post_login_ok_driving':
                pos = self.resolutionCalculator.getPostLoginOkDrivingClick()
            else:
                pos = self.resolutionCalculator.getPostLoginOkPrivatePropertyClick()
            self.vncWrapper.clickVnc(pos.x, pos.y)
            return True
        else:
            log.debug('checkPostLoginOkButton: Could not find OK button')
            return False

    def checkPostLoginOkButton(self, filename, hash):
        return (self.__checkPostLoginOkButton(filename, hash, 'post_login_ok_driving')
            or self.__checkPostLoginOkButton(filename, hash, 'post_login_ok_private_property'))

    #checks the given rows (list of np array of image cropped by bounds) for orange
    def __checkListOfCropOrangeCircle(self, numpyCropList):
        countFound = 0
        for row in numpyCropList:
            for px in row:
                #check the pixel colours...
                if ((px[0] == 162 and px[1] == 193 and px[2] == 254)
                    or (px[0] == 163 and px[1] == 194 and px[2] == 254)):
                    countFound += 1
        if countFound > 3:
            #we found a 2 raid screenshot
            log.debug("__checkListOfCropOrangeCircle: given crop contains circle")
            return True
        else:
            return False

    def readAmountOfRaidsDirect(self, filename, hash):
        if not os.path.isfile(filename):
            return None

        log.debug("readAmountOfRaidsDirect: Cropping circle (orange)")
        screenshotRead = cv2.imread(filename)
        bounds = self.resolutionCalculator.getRaidcountBounds()
        log.debug("readAmountOfRaidsDirect: bounds are %s" % str(bounds))
        raidCount = screenshotRead[bounds.top : bounds.bottom, bounds.left : bounds.right]
        tempPathColoured = self.tempDirPath + "/" + str(hash) + "_raidcount.png"
        cv2.imwrite(tempPathColoured, raidCount)

        raidCountColoured = Image.open(tempPathColoured)
        width, height = raidCountColoured.size

        #check for most present colours... if there's no orange, we can stop immediately
        mostPresentColour = self.__mostPresentColour(tempPathColoured, width * height)
        if (mostPresentColour != (255, 120, 55)):
            log.info("readAmountOfRaidsDirect: No raidcount found, assuming no raids nearby")
            #cv2.imwrite(str(hash) + "_derp.png", raidCount)
            return 0

        tempPath = self.tempDirPath + "/" + str(hash) + "_raidintersect.png"
        #at least one raid, let's start evaluating positions and pixels, yay
        #first check for 2 raids, those are shifted.
        #simply check intersection of firstCheckHorizontal with first vertical of One raid
        #left, middle, right intersecting the checkHorizontal
        #checkHorizontal is a line crossing the orange circle...

        #calculate height of bounds in px
        #TODO: move this all to res calc?
        firstCheckHorizontal = self.resolutionCalculator.getFirstHorizontalPxPosition()

        twoRaidVerticalCheck = self.resolutionCalculator.getRaidBoundsSingle().left
        areaToCheck = screenshotRead[firstCheckHorizontal - 3 : firstCheckHorizontal + 3,
            twoRaidVerticalCheck - 3 : twoRaidVerticalCheck + 3]

        if self.__checkListOfCropOrangeCircle(areaToCheck.tolist()):
            log.debug("Determined screenshot to have 2 raids.")
            return 2

        boundsOne = self.resolutionCalculator.getRaidBoundsTwo(1)
        boundsTwo = self.resolutionCalculator.getRaidBoundsTwo(2)
        verticalChecks = [boundsOne.left, boundsOne.right, boundsTwo.right]
        secondCheckHorizontal = self.resolutionCalculator.getSecondHorizontalPxPosition()

        countOfRaids = 0
        for verticalCheck in verticalChecks:
            #first row
            posToCheck = screenshotRead[firstCheckHorizontal - 3 : firstCheckHorizontal + 3,
                verticalCheck - 3 : verticalCheck + 3]
            if self.__checkListOfCropOrangeCircle(posToCheck.tolist()):
                countOfRaids += 1
            #second row
            posToCheckTwo = screenshotRead[secondCheckHorizontal - 3 : secondCheckHorizontal + 3,
                verticalCheck - 3 : verticalCheck + 3]
            if self.__checkListOfCropOrangeCircle(posToCheckTwo.tolist()):
                countOfRaids += 1

        if countOfRaids == 0:
            return -1 #raidcounter present but no raidcounts below, definitely a bug
        else:
            return countOfRaids

    def readAmountOfRaids(self, filename, hash):
        if not os.path.isfile(filename):
            return None

        log.debug("readAmountOfRaids: Cropping the number inside the circle showing raidcount")
        screenshotRead = cv2.imread(filename)
        bounds = self.resolutionCalculator.getRaidcountBounds()
        log.debug("readAmountOfRaids: bounds are %s" % str(bounds))
        raidCount = screenshotRead[bounds.top : bounds.bottom, bounds.left : bounds.right]
        tempPathColoured = self.tempDirPath + "/" + str(hash) + "_raidcount.png"
        cv2.imwrite(tempPathColoured, raidCount)

        raidCountColoured = Image.open(tempPathColoured)
        width, height = raidCountColoured.size

        #check for most present colours... if there's no orange, we can stop immediately
        mostPresentColour = self.__mostPresentColour(tempPathColoured, width * height)
        if (mostPresentColour != (255, 120, 55)):
            log.info("readAmountOfRaids: No raidcount found, assuming no raids nearby")
            #cv2.imwrite(str(hash) + "_derp.png", raidCount)
            return 0

        tempPathBw = self.tempDirPath + "/" + str(hash) + "_raidcount_bw.png"
        gray = raidCountColoured.convert('L')
        bw = gray.point(lambda x: 0 if x<200 else 255, '1')
        bw.save(tempPathBw)
        text = image_to_string(Image.open(tempPathBw),config='--psm 6 --oem 3').replace(' ', '').replace('~','').replace('o','0').replace('O','0').replace('-','').replace('.','').replace(',','').replace('‘','')

        count = None
        try:
            count = int(text)
        except ValueError:
            #Handle exception when tesseract read bullshit...
            log.info("readAmountOfRaids: could not read a number... " +
                "Text read: %s. Fallback to 6" % text)
            return 6 #we do read 1 and 2 pretty good... 3 gives us trouble, just assume 6 to be good to go

        log.debug("readAmountOfRaids: read raidcount of %s" % str(count))

        return count


    def checkPostLoginNewsMessage(self, filename, hash):
        if not os.path.isfile(filename):
            return False

        log.debug('checkPostLoginNewsMessage: Checking for small news popup ...')
        col = cv2.imread(filename)
        bounds = self.resolutionCalculator.getPostLoginNewsMessageBounds()
        log.debug('checkPostLoginNewsMessage: bounds are %s' % str(bounds))
        raidtimer = col[bounds.top:bounds.bottom, bounds.left:bounds.right]
        tempPathColoured = self.tempDirPath + "/" + str(hash) + "_message.png"
        cv2.imwrite(tempPathColoured, raidtimer)


        col = Image.open(tempPathColoured)
        width, height = col.size

        #check for the colour of the button that says "show all"
        if (self.__mostPresentColour(tempPathColoured, width * height) != (241, 255, 237)):
            return False


        gray = col.convert('L')
        bw = gray.point(lambda x: 0 if x<210 else 255, '1')
        bw.save(self.tempDirPath + "/" + str(hash) + "_cropped_message_bw.png")

        text = image_to_string(Image.open(self.tempDirPath + "/" + str(hash) + "_cropped_message_bw.png"),config='--psm 7')

        #cleanup
        os.remove(self.tempDirPath + "/" + str(hash) + "_cropped_message_bw.png")
        os.remove(self.tempDirPath + "/" + str(hash) + "_message.png")

        log.debug("checkPostLoginNewsMessage: found the following text: %s " % text)
        if len(text) > 1:
            log.debug('checkPostLoginNewsMessage: found popup - closing ...')
            self.vncWrapper.rightClickVnc()
            #os.remove(filename)
            return True
        else:
            log.debug('checkPostLoginNewsMessage: no popup found')
            return False


    def __checkRaidTabOnScreen(self, filename, hash):
        if not os.path.isfile(filename):
            return False

        log.debug('__checkRaidTabOnScreen: Checking for raidscreen ...')
        col = cv2.imread(filename)
        bounds = self.resolutionCalculator.getNearbyRaidTabBounds()
        log.debug("__checkRaidTabOnScreen: Bounds %s" % str(bounds))
        raidtimer = col[bounds.top:bounds.bottom, bounds.left:bounds.right]
        cv2.imwrite(self.tempDirPath + "/" + str(hash) + "_message.png", raidtimer)
        col = Image.open(self.tempDirPath + "/" + str(hash) + "_message.png")
        gray = col.convert('L')
        bw = gray.point(lambda x: 0 if x<210 else 255, '1')
        bw.save(self.tempDirPath + "/" + str(hash) + "_cropped_message_bw.png")

        text = image_to_string(Image.open(self.tempDirPath + "/" + str(hash) + "_cropped_message_bw.png"), config='-c tessedit_char_whitelist=RAID -psm 7')
        log.debug("__checkRaidTabOnScreen: Check for raidtab present resulted in text: %s" % text)

        os.remove('temp/' + str(hash) + '_cropped_message_bw.png')
        os.remove('temp/' + str(hash) + '_message.png')
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
            pos = self.resolutionCalculator.getNearbyRaidTabClick()
            self.vncWrapper.clickVnc(pos.x, pos.y)
            #self.vncWrapper.clickVnc(500, 370) #TODO: adaptive to resolution
            log.debug('checkRaidscreen: RAID-tab found')
            return True
        else:
            log.warning('checkRaidscreen: Could not locate RAID-tab')
            return False

    def checkNearby(self, filename, hash):
        if not self.__checkRaidTabOnScreen(filename, hash):
            #RAID Tab not visible => not on Nearby screen
            log.info('Raidscreen not running...')
            posNearby = self.resolutionCalculator.getNearbyClick()
            self.vncWrapper.clickVnc(posNearby.x, posNearby.y)
            posRaids = self.resolutionCalculator.getNearbyRaidTabClick()
            self.vncWrapper.clickVnc(posRaids.x, posRaids.y)
            return False
        else:
            log.info('Nearby already open')
            return True

    def checkGameQuitPopup(self, filename, hash):
        if not os.path.isfile(filename):
            return False

        log.debug('checkGameQuitPopup: Checking for quit-game popup ...')
        col = cv2.imread(filename)
        bounds = self.resolutionCalculator.getQuitGamePopupBounds()
        quitGameCrop = col[bounds.top:bounds.bottom, bounds.left:bounds.right]
        tempPath = 'temp/' + str(hash) + '_quitbutton.png'
        cv2.imwrite(tempPath, quitGameCrop)

        col = Image.open(tempPath)
        width, height = col.size

        mostPresentColour = self.__mostPresentColour(tempPath, width * height)
        log.debug('checkGameQuitPopup: most present colour is %s' % str(mostPresentColour))
        #just gonna check the most occuring colours on that button...
        if (mostPresentColour != (255, 255, 255)):
            return False

        gray = col.convert('L')
        bw = gray.point(lambda x: 0 if x<210 else 255, '1')
        bw.save(self.tempDirPath + "/" + str(hash) + "_cropped_quitmessage_bw.png")

        text = image_to_string(Image.open(self.tempDirPath + "/" + str(hash) + "_cropped_quitmessage_bw.png"),config='-c tessedit_char_whitelist=X -psm 7')

        #cleanup
        os.remove(self.tempDirPath + "/" + str(hash) + "_cropped_quitmessage_bw.png")
        os.remove(self.tempDirPath + "/" + str(hash) + "_quitbutton.png")

        log.debug("checkGameQuitPopup: Found text: %s " % text)
        if len(text) > 1:
            log.info('checkGameQuitPopup: Found quit popup - aborting quit ...')
            self.vncWrapper.rightClickVnc()
            return True
        else:
            log.debug('checkGameQuitPopup: Could not find quit popup')
            return False

    def checkSpeedwarning(self, filename, hash):
        if not os.path.isfile(filename):
            return False

        log.debug('checkSpeedwarning: Checking for speed-warning ...')
        col = cv2.imread(filename)
        bounds = self.resolutionCalculator.getSpeedwarningBounds()
        log.debug('checkSpeedwarning: got bounds %s' % str(bounds))
        cropOfSpeedwarning = col[bounds.top:bounds.bottom, bounds.left:bounds.right]
        tempPath = self.tempDirPath + "/" + str(hash) + "_speedmessage.png"
        cv2.imwrite(tempPath, cropOfSpeedwarning)

        col = Image.open(tempPath)
        width, height = col.size

        mostPresentColour = self.__mostPresentColour(tempPath, width * height)
        log.debug('checkSpeedwarning: most present colour is %s' % str(mostPresentColour))
        #just gonna check the most occuring colours on that button...
        if (mostPresentColour != (144, 217, 152)
            and mostPresentColour != (146, 217, 152)
            and mostPresentColour != (152, 218, 151)
            and mostPresentColour != (153, 218, 151)
            and mostPresentColour != (151, 218, 151)
            and mostPresentColour != (77, 209, 163)
            and mostPresentColour != (255, 255, 255)):
            return False

        gray = col.convert('L')
        bw = gray.point(lambda x: 0 if x<210 else 255, '1')
        bw.save(self.tempDirPath + "/" + str(hash) + "_cropped_speedmessage_bw.png")

        passengerString = image_to_string(Image.open(self.tempDirPath + "/" + str(hash) + "_cropped_speedmessage_bw.png"),config='-psm 7')

        #cleanup
        os.remove(self.tempDirPath + "/" + str(hash) + "_cropped_speedmessage_bw.png")
        os.remove(self.tempDirPath + "/" + str(hash) + "_speedmessage.png")

        log.debug("checkSpeedwarning: Found text: %s " % passengerString)
        if len(passengerString) > 4:
            log.debug('checkSpeedwarning: Found Speedmessage - closing ...')
            posPassenger = self.resolutionCalculator.getSpeedwarningClick()
            log.debug("checkSpeedwarning: Clicking %s" % str(posPassenger))
            self.vncWrapper.clickVnc(posPassenger.x, posPassenger.y)
            return True
        else:
            log.debug('checkSpeedwarning: No speedmessage found')
            return False

    def checkWeatherWarning(self, filename, hash):
        if not os.path.isfile(filename):
            return False

        log.debug('checkWeatherwarning: Checking for weather-warning ...')
        col = cv2.imread(filename)
        bounds = self.resolutionCalculator.getWeatherWarningBounds()
        log.debug('checkWeatherwarning: got bounds %s' % str(bounds))
        cropOfWeatherwarning = col[bounds.top:bounds.bottom, bounds.left:bounds.right]
        tempPath = self.tempDirPath + "/" + str(hash) + "_weatherwarning.png"
        cv2.imwrite(tempPath, cropOfWeatherwarning)

        col = Image.open(tempPath)
        width, height = col.size

        mostPresentColour = self.__mostPresentColour(tempPath, width * height)
        log.debug('checkWeatherwarning: most present colour is %s' % str(mostPresentColour))
        #just gonna check the most occuring colours on that button...
        if (mostPresentColour != (144, 217, 152)
            and mostPresentColour != (146, 217, 152)
            and mostPresentColour != (145, 217, 152)
            and mostPresentColour != (152, 218, 151)
            and mostPresentColour != (153, 218, 151)
            and mostPresentColour != (151, 218, 151)
            and mostPresentColour != (77, 209, 163)
            and mostPresentColour != (255, 255, 255)
            and mostPresentColour != (228, 255, 222)):
            return False

        gray = col.convert('L')
        bw = gray.point(lambda x: 0 if x<210 else 255, '1')
        bw.save(self.tempDirPath + "/" + str(hash) + "_cropped_weatherwarning_bw.png")

        passengerString = image_to_string(Image.open(self.tempDirPath + "/" + str(hash) + "_cropped_weatherwarning_bw.png"),config='-psm 7')

        #cleanup
        os.remove(self.tempDirPath + "/" + str(hash) + "_cropped_weatherwarning_bw.png")
        os.remove(self.tempDirPath + "/" + str(hash) + "_weatherwarning.png")

        log.debug("checkWeatherwarning: Found text: %s " % passengerString)
        if len(passengerString) > 4:
            log.debug('checkWeatherwarning: Found weather warning - closing ...')
            posPassenger = self.resolutionCalculator.getWeatherWarningFirstClick()
            log.debug("checkWeatherwarning: Clicking %s" % str(posPassenger))
            self.vncWrapper.clickVnc(posPassenger.x, posPassenger.y)
            time.sleep(1)
            log.debug('checkWeatherwarning: Also closing the weather info ...')
            posPassenger = self.resolutionCalculator.getWeatherWarningSecondClick()
            log.debug("checkWeatherwarning: Clicking %s" % str(posPassenger))
            self.vncWrapper.clickVnc(posPassenger.x, posPassenger.y)
            return True
        else:
            log.debug('checkWeatherwarning: No weatherwarning found')
            return False


    def __checkClosePresent(self, filename, hash, windowsToCheck):
        if not os.path.isfile(filename):
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
        tempPath = self.tempDirPath + "/" + str(hash) + "_xbutton.png"
        log.debug("TempPath: %s" % tempPath)
        cv2.imwrite(tempPath, closeButton)

        im = Image.open(tempPath)
        width, height = im.size

        mostPresentColour = self.__mostPresentColour(tempPath, width * height)

        os.remove(self.tempDirPath + "/" + str(hash) + "_xbutton.png")
        return ((mostPresentColour == (28, 135, 150))
            or (mostPresentColour == (236, 252, 235)))

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
            self.vncWrapper.rightClickVnc()
            return True
        else:
            log.debug("Could not find close button (X).")
            return False
