import cv2
import os
import numpy as np
import imutils

def fort_image_matching(url_img_name, fort_img_name, zoom, ttest):
    url_img = cv2.imread(url_img_name,3)
    fort_img = cv2.imread(fort_img_name,3)
    height, width, channels = url_img.shape
    height_f, width_f, channels_f = fort_img.shape

    if zoom == True:
        if width_f == 160:
            fort_img = cv2.resize(fort_img,None,fx=3, fy=3, interpolation = cv2.INTER_NEAREST)
        else:
            fort_img = fort_img[int((height_f/2)-(height_f/3)):int((height_f/2)+(height_f/3)), int((width_f/2)-(width_f/3)):int((width_f/2)+(width_f/3))]

        url_img = cv2.resize(url_img,None,fx=2, fy=2, interpolation = cv2.INTER_NEAREST)
        crop = url_img[int(80):int(200),int(80):int(110)]
    else:
        fort_img = cv2.resize(fort_img,None,fx=2, fy=2, interpolation = cv2.INTER_NEAREST)
        crop = url_img

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
        #print maxVal
        if found is None or maxVal > found[0]:
	        found = (maxVal, maxLoc, r)


    if found[0] < ttest:
        return 0.0

    return found[0]

if __name__ == '__main__':
    fort_id = 'raid1'
    fort_img_path = os.getcwd() + '/' + str(fort_id) + '.jpg'
    url_img_path = os.getcwd() + '/mon_img/ic_raid_egg_rare.png'
    print(fort_image_matching(url_img_path,fort_img_path,True))
