import cv2
import numpy as np
import logging 
cap = cv2.VideoCapture(0)
from PIL import Image
import pytesseract
from getVNCPic import clickVNC, rightClickVNC

log = logging.getLogger(__name__)


def check_login():
    log.info('Check for Loginbutton - start ...')
    col = cv2.imread("screenshot.png")
    raidtimer = col[745:785, 310:400]
    cv2.imwrite("login.png", raidtimer)
    col = Image.open("login.png")
    gray = col.convert('L')
    bw = gray.point(lambda x: 0 if x<210 else 255, '1')
    bw.save("cropped_login_bw.png")
    
    timer2 = pytesseract.image_to_string(Image.open("cropped_login_bw.png"),config='-c tessedit_char_whitelist=O.K. -psm 4', lang='eng')
    log.error(timer2)
    if 'O. K.' in timer2:
        log.info('Found Loginbutton - closing ...')
        clickVNC(340, 750)
    
    log.info('Check for Loginbutton - finished...')

def check_message():
    log.info('Check for Messagebox - start ...')
    col = cv2.imread("screenshot.png")
    raidtimer = col[670:715, 220:480]
    cv2.imwrite("message.png", raidtimer)
    col = Image.open("message.png")
    gray = col.convert('L')
    bw = gray.point(lambda x: 0 if x<210 else 255, '1')
    bw.save("cropped_message_bw.png")
    
    timer2 = pytesseract.image_to_string(Image.open("cropped_message_bw.png"),config='-psm 10')
    log.error(timer2)
    if len(timer2) > 1:
        log.info('Found Messagebox - closing ...')
        rightClickVNC()
        
    log.info('Check for Messagebox - finished...')
    
    
def check_Xbutton():
    log.info('Check for Xbutton - start ...')
    col = cv2.imread("screenshot.png")
    raidtimer = col[1170:1200, 340:380]
    cv2.imwrite("xbutton.png", raidtimer)
    raidtimer2 = col[350:400, 450:600]
    cv2.imwrite("raidscreen.png", raidtimer2)


    col = Image.open("xbutton.png")
    gray = col.convert('L')
    bw = gray.point(lambda x: 0 if x<150 else 255, '1')
    bw.save("cropped_xbutton_bw.png")
    timer2 = pytesseract.image_to_string(Image.open("cropped_xbutton_bw.png"), config='-psm 10')
    
    col = Image.open("raidscreen.png")
    gray = col.convert('L')
    bw = gray.point(lambda x: 0 if x<210 else 255, '1')
    bw.save("cropped_raidscreen_bw.png")
    timer3 = pytesseract.image_to_string(Image.open("cropped_raidscreen_bw.png"), config='-psm 4')
    
    log.error(timer2)
    log.error(timer3)
    if 'X' in timer2 and 'RAID' not in timer3 :
        log.info('Found Xbutton - closing ...')
        rightClickVNC()
        
    log.info('Check for Xbutton - finished...')