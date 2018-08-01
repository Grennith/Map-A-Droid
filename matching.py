import cv2
import os
import numpy as np
import imutils
import logging
import time
from PIL import Image

log = logging.getLogger(__name__)

def fort_image_matching(url_img_name, fort_img_name, zoom, value, raidNo, hash, x1=50, x2=80, y1=100, y2=160):
    #log.debug("fort_image_matching: Reading url_img_name '%s'" % str(url_img_name))
    url_img = cv2.imread(url_img_name,3)
    if (url_img is None):
        log.error('[Crop: ' + str(raidNo) + ' (' + str(hash) +') ] ' + 'fort_image_matching: %s appears to be corrupted' % str(url_img_name))
        return 0.0

    #log.debug("fort_image_matching: Reading fort_img_name '%s'" % str(fort_img_name))
    fort_img = cv2.imread(fort_img_name,3)
    if (fort_img is None):
        log.error('[Crop: ' + str(raidNo) + ' (' + str(hash) +') ] ' + 'fort_image_matching: %s appears to be corrupted' % str(fort_img_name))
        return 0.0
    height, width, channels = url_img.shape
    height_f, width_f, channels_f = fort_img.shape

    if zoom == True:
        if width_f < 180:
            tempFile = str(hash) + "_resize_" + str(raidNo) +".jpg"   
            img_temp = Image.open(fort_img_name)
            wsize = int((float(img_temp.size[0]))*2.5)
            hsize = int((float(img_temp.size[1]))*2.5)
            img_temp = img_temp.resize((wsize,hsize), Image.ANTIALIAS)
            img_temp.save(tempFile)
            fort_img = cv2.imread(tempFile,3)
            os.remove(tempFile)
        else:
            if height_f > width_f:            
                fort_img = fort_img[int((height_f/2)-(height_f/3)):int((height_f/2)+(height_f/3)), int(0):int(width_f)]
            else:
                fort_img = fort_img[int(0):int(height_f), int((width_f/2)-(width_f/3)):int((width_f/2)+(width_f/3))]
            #fort_img = fort_img
            #cv2.imwrite('Gym_' + str(fort_img_name) + '.png', fort_img)
            
        tempFile = str(hash) + "_resize_" + str(raidNo) +".jpg"   
        img_temp = Image.open(url_img_name)
        wsize = int((float(img_temp.size[0]))*1.5)
        hsize = int((float(img_temp.size[1]))*1.5)
        img_temp = img_temp.resize((wsize,hsize), Image.ANTIALIAS)
        img_temp.save(tempFile)
        
        url_img = cv2.imread(tempFile,3)
        #url_img = cv2.resize(url_img,None,fx=2, fy=2, interpolation = cv2.INTER_NEAREST)
        crop = url_img[int(y1):int(y2),int(x1):int(x2)]
        #crop = cv2.resize(url_img,None,fx=2, fy=2, interpolation = cv2.INTER_NEAREST)
        #cv2.imwrite('Crop_' + str(time.time()) + '.png', crop)
        os.remove(tempFile)
    else:
        tempFile = str(hash) + "_resize_" + str(raidNo) +".jpg"   
        img_temp = Image.open(fort_img_name)
        wsize = int((float(img_temp.size[0]))*1.5)
        hsize = int((float(img_temp.size[1]))*1.5)
        img_temp = img_temp.resize((wsize,hsize), Image.ANTIALIAS)
        img_temp.save(tempFile)
        fort_img = cv2.imread(tempFile,3)
        crop = url_img
        os.remove(tempFile)

    if crop.mean() == 255 or crop.mean() == 0:
        return 0.0

    (tH, tW) = crop.shape[:2]

    found = None
    for scale in np.linspace(0.2, 1.0, 20)[::-1]:

        resized = imutils.resize(fort_img, width = int(fort_img.shape[1] * scale))
        r = fort_img.shape[1] / float(resized.shape[1])

        if resized.shape[0] < tH or resized.shape[1] < tW:
            break

        result = cv2.matchTemplate(resized, crop, cv2.TM_CCOEFF_NORMED)
        (_, maxVal, _, maxLoc) = cv2.minMaxLoc(result)
        log.debug('[Crop: ' + str(raidNo) + ' (' + str(hash) +') ] ' + 'Filename: ' + str(url_img_name) + ' Matchvalue: ' + str(maxVal))

        
        if found is None or maxVal > found[0]:
	        found = (maxVal, maxLoc, r)

    if found[0] < value:
        return 0.0

    return found[0]

if __name__ == '__main__':
    fort_id = 'raid1'
    fort_img_path = os.getcwd() + '/' + str(fort_id) + '.jpg'
    url_img_path = os.getcwd() + '/mon_img/ic_raid_egg_rare.png'
    print(fort_image_matching(url_img_path,fort_img_path,True))
