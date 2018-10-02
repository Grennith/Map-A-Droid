import numpy as np
import cv2
from matplotlib import pyplot as plt
from walkerArgs import parseArgs
import logging
log = logging.getLogger(__name__)

args = parseArgs()

def gym_matching(raidcrop, gym, raidNo, hash):


    raidcrop_image = cv2.imread(raidcrop,0)
    if (raidcrop_image is None):
        log.error('[Crop: ' + str(raidNo) + ' (' + str(hash) +') ] ' + 'fort_image_matching: %s appears to be corrupted' % str(raidcrop_image))
        return 0
        
    gym_image = cv2.imread(gym,0)
    if (gym_image is None):
        log.error('[Crop: ' + str(raidNo) + ' (' + str(hash) +') ] ' + 'fort_image_matching: %s appears to be corrupted' % str(gym_image))
        return 0

    sift = cv2.xfeatures2d.SIFT_create()

    kp1, des1 = sift.detectAndCompute(raidcrop_image,None)
    kp2, des2 = sift.detectAndCompute(gym_image,None)


    FLANN_INDEX_KDTREE = 0
    index_params = dict(algorithm = FLANN_INDEX_KDTREE, trees = 5)
    search_params = dict(checks=50)   # or pass empty dictionary
    flann = cv2.FlannBasedMatcher(index_params,search_params)
    matches = flann.knnMatch(des1,des2,k=2)
    #matchesMask = [[0,0] for i in xrange(len(matches))]

    good = []

    for i,(m,n) in enumerate(matches):
        if m.distance < 0.7*n.distance:
            good.append(m)

    log.debug('[Crop: ' + str(raidNo) + ' (' + str(hash) +') ] ' + 'Filename: ' + str(gym) + ' Matchcount: ' + str(len(good)))
    
    return len(good)


