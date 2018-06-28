import cv2
import os
import numpy as np
import imutils
import os
import os.path
import logging

log = logging.getLogger(__name__)

def copyMons():
    
    log.info('Processing Pokemon Matching....')
    
    monImgPath = os.getcwd() + '/mon_img/'
    filePath = os.path.dirname(monImgPath)
    
    if not os.path.exists(filePath):
        LOG.info('mon_img directory created')
        os.makedirs(filePath)
            
    assetPath = '../PogoAssets/decrypted_assets/'
    raidMons = ["50", "150", "350", "95", "378"]
    
    if not os.path.exists(assetPath):
        log.error('PogoAssets not found')
        exit(0)
    
    for mon in raidMons:
        
        mon = '{:03d}'.format(int(mon))
        monFile = monImgPath + 'mon_' + str(mon) + '.png'
        
        if not os.path.isfile(monFile):
            
            log.info('Processing Pokedex Nr: ' + str(mon))
            
            monFileAsset = assetPath + 'pokemon_icon_' + str(mon) + '_00.png'
            
            if not os.path.isfile(monFileAsset):
                log.error('File ' + str(monFileAsset) + ' not found')
                exit(0)
                
            
            read_transparent_png(monFileAsset, monFile)
            
            monAsset = cv2.imread(monFile,3)
            height, width, channels = monAsset.shape
            monAsset = cv2.inRange(monAsset,np.array([255,255,255]),np.array([255,255,255]))
            cv2.imwrite(monFile, monAsset)
            crop = cv2.imread(monFile,3)        
            crop = crop[0:int(height), 0:int(width/2)]
            cv2.imwrite(monFile, crop)
            log.info('Processing Pokemon Nr: ' + str(mon) + ' finished')


def read_transparent_png(assetFile, monFile):
    image_4channel = cv2.imread(assetFile, cv2.IMREAD_UNCHANGED)
    alpha_channel = image_4channel[:,:,3]
    rgb_channels = image_4channel[:,:,:3]

    white_background_image = np.ones_like(rgb_channels, dtype=np.uint8) * 255

    alpha_factor = alpha_channel[:,:,np.newaxis].astype(np.float32) / 255.0
    alpha_factor = np.concatenate((alpha_factor,alpha_factor,alpha_factor), axis=2)

    base = rgb_channels.astype(np.float32) * alpha_factor
    white = white_background_image.astype(np.float32) * (1 - alpha_factor)
    final_image = base + white
    
    cv2.imwrite(monFile,final_image.astype(np.uint8))
    
    return assetFile 
     
if __name__ == '__main__':
    copyMons()

    