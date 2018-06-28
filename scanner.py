import cv2
import numpy as np
import argparse
cap = cv2.VideoCapture(0)
from PIL import Image
import pytesseract
import datetime
import time
import matching as mt

Y1 = 585
Y2 = 908

X1 = 161
X2 = 380
X3 = 598



from skimage.measure import compare_ssim as ssim
import glob, os
import mysql;
import mysql.connector;

def compare_images(imageA, imageB, guid, pkm, lvl):
    #s = ssim(imageA, imageB)
    m = mse(imageA, imageB)



#    print str() + " " + title + str(s) + " " + str(m)
    if m < 205:
        raidfound = 1
        col = Image.open("raidtimer.jpg")
        gray = col.convert('L')
        bw = gray.point(lambda x: 0 if x<185 else 255, '1')
        bw.save("cropped_timer_bw.jpg")
    
        timer = pytesseract.image_to_string(Image.open("cropped_timer_bw.jpg"),config='digits')
        timer2 = pytesseract.image_to_string(Image.open("cropped_timer_bw.jpg"),config='text')

        #out_text =  "\n\n" + "Latias Raid found at Gym: " + title + " Starting at " + timer +"\n"
        #print(out_text)

        if "Raid" not in timer2:

            aab = datetime.datetime(100,1,1,int(timer[:2]),int(timer[-2:]),00)
            bba = aab - datetime.timedelta(0,7200) # days, seconds, then other fields.
            raidstart = date1 + " " + str(bba.time()) 

            print(raidstart)

            a = datetime.datetime(100,1,1,int(timer[:2]),int(timer[-2:]),00)
            b = a - datetime.timedelta(0,4500) # days, seconds, then other fields.
            raidend = date1 + " " + str(b.time()) 
        
        else:
            raidstart = "-"
            
            
        cursor = connection.cursor()
        
        if pkm == 0:
            query = " UPDATE raid SET level = %s, spawn=%s, start=%s, end=%s, pokemon_id = %s, cp = %s, move_1 = %s, move_2 = %s, last_scanned = %s WHERE gym_id = %s "
            data = (lvl, today2, raidstart, raidend, None, "999", "1", "1",  today1, guid)
            cursor.execute(query, data)
        else:
            query = " UPDATE raid SET level = %s, spawn=%s, start=%s, end=%s, pokemon_id = %s, cp = %s, move_1 = %s, move_2 = %s, last_scanned = %s WHERE gym_id = %s "
            data = (lvl, today2, raidstart, raidend, pkm, "999", "1", "1",  today1, guid)
            cursor.execute(query, data)
            
        connection.commit()
        return 1
    

def compare_images2(imageA, imageB):
    #s = ssim(imageA, imageB)
    m = mse(imageA, imageB)
  
    #print "compare 2 " + str(m)
    if m < 260:
        return 1
    else:
        return 0

def mse(imageA, imageB):
	# the 'Mean Squared Error' between the two images is the
	# sum of the squared difference between the two images;
	# NOTE: the two images must have the same dimension
	err = np.sum((imageA.astype("float") - imageB.astype("float")) ** 2)
	err /= float(imageA.shape[0] * imageA.shape[1])
	
	# return the MSE, the lower the error, the more "similar"
	# the two images are
	return err


def start_detect():
    now = datetime.datetime.now()
    date1 = str(now.year) + "-0" + str(now.month) + "-" + str(now.day)
    today1 = date1 + " " + str(now.hour) + ":" + str(now.minute) + ":" + str(now.second)
    today2 = date1 + " 00:01:00"



    img = cv2.imread('screenshot.png')
    img = cv2.resize(img, (750, 1334), interpolation = cv2.INTER_CUBIC) 
###raid1
    raid1 = img[Y1-70:Y1+200,X1-80:X1+80]

    cv2.imwrite("raid1.jpg", raid1)

###raid2
    raid2 = img[Y1-70:Y1+200, X2-80:X2+80]
    cv2.imwrite("raid2.jpg", raid2)

###raid3
    raid3 = img[Y1-70:Y1+200, X3-80:X3+80]
    cv2.imwrite("raid3.jpg", raid3)

###raid4
    raid4 = img[Y2-70:Y2+200, X1-80:X1+80]
    cv2.imwrite("raid4.jpg", raid4)

###raid5
    raid5 = img[Y2-70:Y2+200, X2-80:X2+80]
    cv2.imwrite("raid5.jpg", raid5)

###raid3
    raid6 = img[Y2-70:Y2+200, X3-80:X3+80]
    cv2.imwrite("raid6.jpg", raid6)


    i = 1
    foundgym = None
    foundmon = None

    while i < 6:
        gymfound = 0
        monfound = 0
        image1 = cv2.imread("raid" + str(i) +".jpg")
        raidpic = image1[0:165, 0:160]
        cv2.imwrite("raidpic" + str(i) +".jpg", raidpic)

        image2 = cv2.imread("raid" + str(i) +".jpg")
        raidtimer = image2[200:230, 0:297]
        raidtimer = cv2.resize(raidtimer, (0,0), fx=3, fy=3) 
        cv2.imwrite("raidtimer.jpg", raidtimer)

        raidlevel = image2[235:265, 0:297]
        raidlevel = cv2.resize(raidlevel, (0,0), fx=3, fy=3) 
        cv2.imwrite("raidlevel" + str(i) +".jpg", raidlevel)
    
        lower = np.array([86, 31, 4], dtype = "uint8")
    	upper = np.array([220, 88, 50], dtype = "uint8")
    	mask = cv2.inRange(image2, lower, upper)
    	output = cv2.bitwise_and(image2, image2, mask = mask)
        cv2.imwrite("raidboss" + str(i) +".jpg", output)
        monAsset = cv2.imread("raidboss" + str(i) +".jpg",3)
        monAsset = cv2.inRange(monAsset,np.array([0,0,0]),np.array([15,15,15]))
        cv2.imwrite("raidboss" + str(i) +".jpg", monAsset)

        emptyraid = image2[195:225, 0:160]
        cv2.imwrite("emptyraid.png", raidtimer)
        rt = Image.open("emptyraid.png")
        gray = rt.convert('L')
        bw = gray.point(lambda x: 0 if x<210 else 255, '1')
        bw.save("cropped_emptyraid_bw.png")
        raidtext = pytesseract.image_to_string(Image.open("cropped_emptyraid_bw.png"),config='-psm 7')
	
# load the images -- the original, the original + contrast,
# and the original + photoshop
        original = cv2.imread("raidpic" + str(i) +".jpg",3)
        original = cv2.cvtColor(cv2.imread("raidpic" + str(i) +".jpg"), cv2.COLOR_BGR2GRAY)
        original2 = cv2.cvtColor(cv2.imread("raidpic" + str(i) +".jpg"), cv2.COLOR_BGR2GRAY)
        raidlvl  = cv2.cvtColor(cv2.imread("raidlevel" + str(i) +".jpg"), cv2.COLOR_BGR2GRAY)
      
    #raidboss  = cv2.cvtColor(cv2.imread("raidboss.jpg"), cv2.COLOR_BGR2GRAY)

#gyms

    
        for file in glob.glob("gym_img/*.jpg"):      
            find_gym = mt.fort_image_matching("raid" + str(i) +".jpg", file, True)
            if foundgym is None or find_gym > foundgym[0]:
	    		foundgym = (find_gym, file)

        if not foundgym is None and foundgym[0]>0.8 and len(raidtext) > 0:
            gymfound = 1

        for file in glob.glob("mon_img/*.png"): 
            find_mon = mt.fort_image_matching(file, "raidboss" + str(i) +".jpg", False)
            if foundmon is None or find_mon > foundmon[0]:
	    		foundmon = (find_mon, file)
 
        if not foundmon is None and foundmon[0]>0.8 and len(raidtext) > 0:
            monfound = 1          

        if gymfound == 1 and monfound == 1:
            print('Gym - ID: ' + str(foundgym[1]))
            print('Mon - ID: ' + str(foundmon[1]))

##############################################
        if gymfound == 0 and len(raidtext) > 0:
            unknowngymfound = 0
            for file in glob.glob("unknown/gym_*.jpg"):
            
                        foundunknowngym = mt.fort_image_matching("raidpic" + str(i) +".jpg", file, True)  
                        if foundgym is None or foundunknowngym > foundgym[0]:
            	    		foundgym = (foundunknowngym, file)
                        
                        if not foundgym is None and foundgym[0]>0.8:
                            unknowngymfound = 1
                            foundgym = None
            
            if unknowngymfound == 0:
                name22 = time.time()
                cv2.imwrite("unknown/gym_" + str(name22) +".jpg", raidpic)	

        if monfound == 0 and len(raidtext) > 0:
            unknownmonfound = 0
            for file in glob.glob("unknown/mon_*.jpg"):

                        foundunknownmon = mt.fort_image_matching("raidboss" + str(i) +".jpg", file, False)
                        if foundmon is None or foundunknownmon > foundmon[0]:
            	    		foundmon = (foundunknownmon, file)
                                
                        
                        if not foundmon is None and foundmon[0]>0.8:
                            unknownmonfound = 1
                            foundmon = None
                            
            if unknownmonfound == 0:
                name22 = time.time()
                cv2.imwrite("unknown/mon_" + str(name22) +".jpg", output)	
                        
        raidtext = None
        i = i+1

	

def detectLevel(level_img):
        level1_num = 228950.0
        level_img = cv2.imread(str(level_img),3)
        img_gray = cv2.cvtColor(level_img,cv2.COLOR_BGR2GRAY)
        ret,thresh1 = cv2.threshold(img_gray,250,255,cv2.THRESH_BINARY_INV)
        height, width, channel = level_img.shape
        scale = width/240
        print(thresh1)
        level = int(cv2.sumElems(thresh1)[0]/(level1_num*scale*scale) + 0.2)
        #cv2.imshow('level', thresh1)
        #cv2.waitKey(0)


        return level
	
if __name__ == '__main__':
    start_detect()
    #print(detectLevel('raidlevel2.jpg'))












