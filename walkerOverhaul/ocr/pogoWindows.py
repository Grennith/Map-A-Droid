import cv2
import numpy as np
import logging
cap = cv2.VideoCapture(0)
from PIL import Image
#import pytesseract
from pytesseract import image_to_string
from resolutionCalculator import *

import os.path
import sys
sys.path.insert(0, '../')
from vnc.vncWrapper import VncWrapper


log = logging.getLogger(__name__)

if not os.path.exists('temp'):
    log.info('Temp directory created')
    os.makedirs('temp')

class PogoWindows:
    def __init__(self, vncIp, vncScreen, vncPort, vncPassword, width, height):
        self.vncWrapper = VncWrapper(str(vncIp), vncScreen, vncPort, vncPassword)
        self.resolutionCalculator = ResolutionCalc(width, height)

    def checkLogin(self, filename, hash):
        result = False
        if not os.path.isfile(filename): #TODO: do not rely on filename
            return result
        log.info('Checking for loginbutton...')
        col = cv2.imread(filename)
        raidtimer = col[740:790, 310:420] #TODO: adaptive to resolution
        cv2.imwrite("temp/" + str(hash) + "_login.png", raidtimer)
        col = Image.open("temp/" + str(hash) + "_login.png")
        gray = col.convert('L')
        bw = gray.point(lambda x: 0 if x<210 else 255, '1')
        bw.save("temp/" + str(hash) + "_cropped_login_bw.png")
        text = image_to_string(Image.open("temp/" + str(hash) + "_cropped_login_bw.png"),config='-c tessedit_char_whitelist=O.K -psm 7')
        log.error(text)
        if 'O. K.' in text:
            log.info('Found Loginbutton - closing ...')
            self.vncWrapper.clickVNC(340, 750) #TODO: adaptive to resolution
            #os.remove(filename)
            result = True
        else:
            log.error('No login detected')
        os.remove("temp/" + str(hash) + "_login.png")
        os.remove("temp/" + str(hash) + "_cropped_login_bw.png")
        return result

    def checkMessage(self, filename, hash):
        result = False
        if not os.path.isfile(filename):
            return result

        log.info('Checking for messagebox ...')
        col = cv2.imread(filename)
        raidtimer = col[670:715, 220:480] #TODO: adaptive to resolution
        cv2.imwrite("temp/" + str(hash) + "_message.png", raidtimer)
        col = Image.open("temp/" + str(hash) + "_message.png")
        gray = col.convert('L')
        bw = gray.point(lambda x: 0 if x<210 else 255, '1')
        bw.save("temp/" + str(hash) + "_cropped_message_bw.png")

        text = image_to_string(Image.open("temp/" + str(hash) + "_cropped_message_bw.png"),config='-psm 10')
        log.error(text)
        if len(text) > 1:
            log.error('Found Messagebox - closing ...')
            self.vncWrapper.rightClickVnc()
            #os.remove(filename)
            result = True
        else:
            log.error('No message found')
        os.remove("temp/" + str(hash) + "_cropped_message_bw.png")
        os.remove("temp/" + str(hash) + "_message.png")
        return result

    def __checkRaidTabOnScreen(self, filename, hash):
        if not os.path.isfile(filename):
            return False

        log.info('Checking for raidscreen ...')
        col = cv2.imread(filename)
        raidtimer = col[350:400, 450:600] #TODO: adaptive to resolution
        cv2.imwrite("temp/" + str(hash) + "_message.png", raidtimer)
        col = Image.open("temp/" + str(hash) + "_message.png")
        gray = col.convert('L')
        bw = gray.point(lambda x: 0 if x<210 else 255, '1')
        bw.save("temp/" + str(hash) + "_cropped_message_bw.png")

        text = image_to_string(Image.open("temp/" + str(hash) + "_cropped_message_bw.png"), config='-c tessedit_char_whitelist=RAID -psm 7')
        log.error(text)

        os.remove('temp/' + str(hash) + '_cropped_message_bw.png')
        os.remove('temp/' + str(hash) + '_message.png')
        #os.remove(filename)
        return 'RAID' in text

    #assumes we are on the general view of the game
    def checkRaidscreen(self, filename, hash):
        result = False
        if self.__checkRaidTabOnScreen(filename, hash):
            #RAID Tab visible
            self.vncWrapper.clickVnc(500, 370) #TODO: adaptive to resolution
            log.error('Raidscreen found')
            result = True
        else:
            log.error('No Raidscreen found')

        return result

    def checkNearby(self, filename, hash):
        result = False
        if not self.__checkRaidTabOnScreen(filename, hash):
            #RAID Tab not visible => not on Nearby screen
            log.info('Raidscreen not running...')
            self.vncWrapper.clickVnc(600, 1170) #TODO: adaptive to resolution
            self.vncWrapper.clickVnc(500, 370) #TODO: adaptive to resolution
            result = False
        else:
            log.error('Nearby already open')
            result = True
        return result

    def checkQuitbutton(self, filename, hash):
        result = False
        if not os.path.isfile(filename):
            return result

        log.info('Check for Quitbutton - start ...')
        col = cv2.imread(filename)
        raidtimer = col[780:830, 240:480] #TODO: adaptive to resolution
        cv2.imwrite('temp/' + str(hash) + '_quitbutton.png', raidtimer)
        col = Image.open("temp/" + str(hash) + "_quitbutton.png")
        gray = col.convert('L')
        bw = gray.point(lambda x: 0 if x<210 else 255, '1')
        bw.save("temp/" + str(hash) + "_cropped_quitmessage_bw.png")

        text = image_to_string(Image.open("temp/" + str(hash) + "_cropped_quitmessage_bw.png"),config='-c tessedit_char_whitelist=X -psm 7')
        log.error(text)
        if len(text) > 1:
            log.info('Found Quitbutton - closing ...')
            self.vncWrapper.rightClickVnc()
            #os.remove(filename)
            result = True
        else:
            log.error('No quit-button found found')

        os.remove("temp/" + str(hash) + "_cropped_quitmessage_bw.png")
        os.remove("temp/" + str(hash) + "_quitbutton.png")
        return result

    def checkSpeedmessage(self, filename, hash):
        result = False
        if not os.path.isfile(filename):
            return result

        log.info('Checking for speed-warning ...')
        col = cv2.imread(filename)
        raidtimer = col[865:915, 190:530] #TODO: adaptive to resolution
        cv2.imwrite("temp/" + str(hash) + "_speedmessage.png", raidtimer)
        col = Image.open("temp/" + str(hash) + "_speedmessage.png")
        gray = col.convert('L')
        bw = gray.point(lambda x: 0 if x<210 else 255, '1')
        bw.save("temp/" + str(hash) + "_cropped_speedmessage_bw.png")

        timer2 = image_to_string(Image.open("temp/" + str(hash) + "_cropped_speedmessage_bw.png"),config='-psm 7')
        log.error(timer2)
        if len(timer2) > 10:
            log.info('Found Speedmessage - closing ...')
            self.vncWrapper.clickVnc(360,900) #TODO: adaptive to resolution
            self.vncWrapper.clickVnc(880, 450) #TODO: adaptive to resolution
            #os.remove(filename)
            result = True
        else:
            log.error('No speedmessage found')
        os.remove("temp/" + str(hash) + "_cropped_speedmessage_bw.png")
        os.remove("temp/" + str(hash) + "_speedmessage.png")
        return result

    def checkClosebutton(self, filename, hash):
        result = False
        if not os.path.isfile(filename):
            return result

        log.info('Checking for close button (X) ...')
        col = cv2.imread(filename)
        raidtimer = col[1170:1200, 340:380] #TODO: adaptive to resolution
        cv2.imwrite("temp/" + str(hash) + "_xbutton.png", raidtimer)
        raidtimer2 = col[350:400, 450:600] #TODO: adaptive to resolution
        cv2.imwrite("temp/" + str(hash) + "_raidscreen.png", raidtimer2)


        col = Image.open("temp/" + str(hash) + "_xbutton.png")
        gray = col.convert('L')
        bw = gray.point(lambda x: 0 if x<150 else 255, '1')
        bw.save("temp/" + str(hash) + "_cropped_xbutton_bw.png")
        text1 = image_to_string(Image.open("temp/" + str(hash) + "_cropped_xbutton_bw.png"), config='-psm 10')

        col = Image.open("temp/" + str(hash) + "_raidscreen.png")
        gray = col.convert('L')
        bw = gray.point(lambda x: 0 if x<210 else 255, '1')
        bw.save("temp/" + str(hash) + "_cropped_raidscreen_bw.png")
        text2 = image_to_string(Image.open("temp/" + str(hash) + "_cropped_raidscreen_bw.png"), config='-c tessedit_char_whitelist=RAID -psm 7')

        log.error(text1)
        log.error(text2)
        if 'X' in text1 and 'RAID' not in text2 :
            log.info('Found Xbutton - closing ...')
            self.vncWrapper.rightClickVnc()
            #os.remove(filename)
            result = True
        else:
            log.error('No closebutton found')
        os.remove("temp/" + str(hash) + "_cropped_raidscreen_bw.png")
        os.remove("temp/" + str(hash) + "_cropped_xbutton_bw.png")
        os.remove("temp/" + str(hash) + "_raidscreen.png")
        os.remove("temp/" + str(hash) + "_xbutton.png")
        return result
