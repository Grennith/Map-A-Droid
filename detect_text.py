import cv2
import numpy as np
import logging 
cap = cv2.VideoCapture(0)
from PIL import Image
import pytesseract
from getVNCPic import clickVNC, rightClickVNC
import os.path

log = logging.getLogger(__name__)

if not os.path.exists('temp'):
    log.info('Temp directory created')
    os.makedirs('temp')

def check_login(filename, hash):
    if not os.path.isfile(filename):
        return
    
    log.info('Check for Loginbutton - start ...')
    col = cv2.imread(filename)
    #raidtimer = col[715:760, 320:410]
    raidtimer = col[740:790, 310:420]
    cv2.imwrite("temp/" + str(hash) + "_login.png", raidtimer)
    col = Image.open("temp/" + str(hash) + "_login.png")
    gray = col.convert('L')
    bw = gray.point(lambda x: 0 if x<210 else 255, '1')
    bw.save("temp/" + str(hash) + "_cropped_login_bw.png")
    
    text = pytesseract.image_to_string(Image.open("temp/" + str(hash) + "_cropped_login_bw.png"),config='-c tessedit_char_whitelist=O.K -psm 7')
    log.error(text)
    if 'O. K.' in text:
        log.info('Found Loginbutton - closing ...')
        clickVNC( 340, 750 )
        os.remove(filename)
    
    os.remove("temp/" + str(hash) + "_login.png")
    os.remove("temp/" + str(hash) + "_cropped_login_bw.png")


def check_message(filename, hash):
    if not os.path.isfile(filename):
        return
        
    log.info('Check for Messagebox - start ...')
    col = cv2.imread(filename)
    raidtimer = col[670:715, 220:480]
    cv2.imwrite("temp/" + str(hash) + "_message.png", raidtimer)
    col = Image.open("temp/" + str(hash) + "_message.png")
    gray = col.convert('L')
    bw = gray.point(lambda x: 0 if x<210 else 255, '1')
    bw.save("temp/" + str(hash) + "_cropped_message_bw.png")
    
    text = pytesseract.image_to_string(Image.open("temp/" + str(hash) + "_cropped_message_bw.png"),config='-psm 10')
    log.error(text)
    if len(text) > 1:
        log.info('Found Messagebox - closing ...')
        rightClickVNC()
        os.remove(filename)
        
    os.remove("temp/" + str(hash) + "_cropped_message_bw.png")
    os.remove("temp/" + str(hash) + "_message.png")
    

def check_raidscreen(filename, hash):
    if not os.path.isfile(filename):
        return
        
    log.info('Check for Raidscreen - start ...')
    col = cv2.imread(filename)
    raidtimer = col[350:400, 450:600]
    cv2.imwrite("temp/" + str(hash) + "_message.png", raidtimer)
    col = Image.open("temp/" + str(hash) + "_message.png")
    gray = col.convert('L')
    bw = gray.point(lambda x: 0 if x<210 else 255, '1')
    bw.save("temp/" + str(hash) + "_cropped_message_bw.png")
    
    text = pytesseract.image_to_string(Image.open("temp/" + str(hash) + "_cropped_message_bw.png"), config='-c tessedit_char_whitelist=RAID -psm 7')
    log.error(text)
    if 'RAID' not in text:
        log.info('Raidscreen not running...')
        clickVNC(600, 1170)
        clickVNC(500, 370)
        os.remove(filename)
    else:
        clickVNC(500, 370)
    
    os.remove('temp/' + str(hash) + '_cropped_message_bw.png')
    os.remove('temp/' + str(hash) + '_message.png')     

def check_quitbutton(filename, hash):
    if not os.path.isfile(filename):
        return
        
    log.info('Check for Quitbutton - start ...')
    col = cv2.imread(filename)
    raidtimer = col[780:830, 240:480]
    cv2.imwrite('temp/' + str(hash) + '_quitbutton.png', raidtimer)
    col = Image.open("temp/" + str(hash) + "_quitbutton.png")
    gray = col.convert('L')
    bw = gray.point(lambda x: 0 if x<210 else 255, '1')
    bw.save("temp/" + str(hash) + "_cropped_quitmessage_bw.png")
    
    text = pytesseract.image_to_string(Image.open("temp/" + str(hash) + "_cropped_quitmessage_bw.png"),config='-c tessedit_char_whitelist=X -psm 7')
    log.error(text)
    if len(text) > 1:
        log.info('Found Quitbutton - closing ...')
        rightClickVNC()
        os.remove(filename)
        
    os.remove("temp/" + str(hash) + "_cropped_quitmessage_bw.png")
    os.remove("temp/" + str(hash) + "_quitbutton.png") 

def check_speedmessage(filename, hash):
    if not os.path.isfile(filename):
        return
        
    log.info('Check for Speedmessage - start ...')
    col = cv2.imread(filename)
    raidtimer = col[865:915, 190:530]
    cv2.imwrite("temp/" + str(hash) + "_speedmessage.png", raidtimer)
    col = Image.open("temp/" + str(hash) + "_speedmessage.png")
    gray = col.convert('L')
    bw = gray.point(lambda x: 0 if x<210 else 255, '1')
    bw.save("temp/" + str(hash) + "_cropped_speedmessage_bw.png")
    
    timer2 = pytesseract.image_to_string(Image.open("temp/" + str(hash) + "_cropped_speedmessage_bw.png"),config='-psm 7')
    log.error(timer2)
    if len(timer2) > 10:
        log.info('Found Speedmessage - closing ...')
        clickVNC(360,900)
        clickVNC(880, 450)
        os.remove(filename)
        
    os.remove("temp/" + str(hash) + "_cropped_speedmessage_bw.png")
    os.remove("temp/" + str(hash) + "_speedmessage.png") 

def check_Xbutton(filename, hash):
    if not os.path.isfile(filename):
        return
        
    log.info('Check for Xbutton - start ...')
    col = cv2.imread(filename)
    raidtimer = col[1170:1200, 340:380]
    cv2.imwrite("temp/" + str(hash) + "_xbutton.png", raidtimer)
    raidtimer2 = col[350:400, 450:600]
    cv2.imwrite("temp/" + str(hash) + "_raidscreen.png", raidtimer2)


    col = Image.open("temp/" + str(hash) + "_xbutton.png")
    gray = col.convert('L')
    bw = gray.point(lambda x: 0 if x<150 else 255, '1')
    bw.save("temp/" + str(hash) + "_cropped_xbutton_bw.png")
    text1 = pytesseract.image_to_string(Image.open("temp/" + str(hash) + "_cropped_xbutton_bw.png"), config='-psm 10')
    
    col = Image.open("temp/" + str(hash) + "_raidscreen.png")
    gray = col.convert('L')
    bw = gray.point(lambda x: 0 if x<210 else 255, '1')
    bw.save("temp/" + str(hash) + "_cropped_raidscreen_bw.png")
    text2 = pytesseract.image_to_string(Image.open("temp/" + str(hash) + "_cropped_raidscreen_bw.png"), config='-c tessedit_char_whitelist=RAID -psm 7')
    
    log.error(text1)
    log.error(text2)
    if 'X' in text1 and 'RAID' not in text2 :
        log.info('Found Xbutton - closing ...')
        rightClickVNC()
        os.remove(filename)
     
    os.remove("temp/" + str(hash) + "_cropped_raidscreen_bw.png")
    os.remove("temp/" + str(hash) + "_cropped_xbutton_bw.png")   
    os.remove("temp/" + str(hash) + "_raidscreen.png")
    os.remove("temp/" + str(hash) + "_xbutton.png")