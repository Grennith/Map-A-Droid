import cv2
import os
import numpy as np
import imutils
import glob, os
import os.path
import logging
from shutil import copyfile
from PIL import Image

log = logging.getLogger(__name__)

class MonRaidImages(object):
    @staticmethod
    def copyMons(pogoasset):

        log.info('Processing Pokemon Matching....')

        monImgPath = os.getcwd() + '/mon_img/'
        filePath = os.path.dirname(monImgPath)

        if not os.path.exists(filePath):
            log.info('mon_img directory created')
            os.makedirs(filePath)

        assetPath = pogoasset
        raidMons = {1: [129, 140, 320, 138], 
                    2: [125, 303, 185, 310],
                    3: [68, 142, 135, 95],
                    4: [359, 248, 76, 112],
                    5: [378]
                }

        if not os.path.exists(assetPath):
            log.error('PogoAssets not found')
            exit(0)

        for file in glob.glob(monImgPath + "*mon*.png"):
                    os.remove(file)

        for lvl, mons in raidMons.iteritems():
            for mon in mons:

                mon = '{:03d}'.format(int(mon))
                monFile = monImgPath + '_mon_' + str(mon) + '_' + str(lvl) + '.png'

                if not os.path.isfile(monFile):

                    monFileAsset = assetPath + 'decrypted_assets/pokemon_icon_' + str(mon) + '_00.png'

                    if not os.path.isfile(monFileAsset):
                        log.error('File ' + str(monFileAsset) + ' not found')
                        exit(0)
                
                    copyfile(monFileAsset, monFile)
            
                    image = Image.open(monFile)
                    image.convert("RGBA")
                    canvas = Image.new('RGBA', image.size, (255,255,255,255)) # Empty canvas colour (r,g,b,a)
                    canvas.paste(image, mask=image) # Paste the image onto the canvas, using it's alpha channel as mask
                    canvas.save(monFile, format="PNG")

                    monAsset = cv2.imread(monFile,3)
                    height, width, channels = monAsset.shape
                    monAsset = cv2.inRange(monAsset,np.array([240,240,240]),np.array([255,255,255]))
                    cv2.imwrite(monFile, monAsset)
                    crop = cv2.imread(monFile,3)
                    crop = crop[0:int(height), 0:int((width/6)*5)]
                    kernel = np.ones((3,3),np.uint8)
                    crop = cv2.erode(crop,kernel,iterations = 1)
                    cv2.imwrite(monFile, crop)

    @staticmethod
    def copyEggs(pogoasset):
        from shutil import copyfile

        log.info('Processing Eggs')

        eggImgPath = os.getcwd() + '/mon_img/'
        filePath = os.path.dirname(eggImgPath)

        if not os.path.exists(filePath):
            LOG.info('mon_img directory created')
            os.makedirs(filePath)

        assetPath = pogoasset
        eggIcons = ['ic_raid_egg_normal.png', 'ic_raid_egg_rare.png', 'ic_raid_egg_legendary.png']
        i = 1
        for egg in eggIcons:

            eggFile = eggImgPath + str('_egg_') + str(i) + '_.png'

            if not os.path.isfile(eggFile):

                log.info('Processing Egg File: ' + str(egg))

                eggFileAsset = assetPath + 'static_assets/png/'+ str(egg)

                if not os.path.isfile(eggFileAsset):
                    log.error('File ' + str(eggFileAsset) + ' not found')
                    exit(0)

                MonRaidImages.read_transparent_png(eggFileAsset, eggFile)

                log.info('Processing Eggfile: ' + str(egg) + ' finished')
                i = i +1

    @staticmethod
    def read_transparent_png(assetFile, saveFile):
        image_4channel = cv2.imread(assetFile, cv2.IMREAD_UNCHANGED)
        alpha_channel = image_4channel[:,:,3]
        rgb_channels = image_4channel[:,:,:3]

        white_background_image = np.ones_like(rgb_channels, dtype=np.uint8) * 255

        alpha_factor = alpha_channel[:,:,np.newaxis].astype(np.float32) / 255.0
        alpha_factor = np.concatenate((alpha_factor,alpha_factor,alpha_factor), axis=2)

        base = rgb_channels.astype(np.float32) * alpha_factor
        white = white_background_image.astype(np.float32) * (1 - alpha_factor)
        final_image = base + white

        cv2.imwrite(saveFile,final_image.astype(np.uint8))

        return assetFile

    @staticmethod
    def runAll(pogoasset):
        MonRaidImages.copyMons(pogoasset)
        MonRaidImages.copyEggs(pogoasset)
        
if __name__ == '__main__':
    MonRaidImages.runAll('../../PogoAssets/')
