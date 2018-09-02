import cv2
import os
import numpy as np
import imutils
import glob, os
import os.path
import logging
import json
from shutil import copyfile
from PIL import Image
from walkerArgs import parseArgs
from db.dbWrapper import DbWrapper

log = logging.getLogger(__name__)
args = parseArgs()


class MonRaidImages(object):

    @staticmethod
    def copyMons(pogoasset):

        monList = []

        log.info('Processing Pokemon Matching....')
        with open('raidmons.json') as f:
            data = json.load(f)

        monImgPath = os.getcwd() + '/mon_img/'
        filePath = os.path.dirname(monImgPath)

        if not os.path.exists(filePath):
            log.info('mon_img directory created')
            os.makedirs(filePath)

        assetPath = pogoasset

        if not os.path.exists(assetPath):
            log.error('PogoAssets not found')
            exit(0)

        for file in glob.glob(monImgPath + "*mon*.png"):
                    os.remove(file)

        for mons in data:
            for mon in mons['DexID']:
                lvl = mons['Level']
                if str(mon).find("_") > -1:
                    mon_split = str(mon).split("_")
                    mon = mon_split[0]
                    frmadd = mon_split[1] 
                else:
                    frmadd = "00"

                mon = '{:03d}'.format(int(mon))
                monList.append(mon)

                monFile = monImgPath + '_mon_' + str(mon) + '_' + str(lvl) + '.png'

                if not os.path.isfile(monFile):

                    monFileAsset = assetPath + '/pokemon_icons/pokemon_icon_' + str(mon) + '_' + frmadd + '.png'

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
                    crop = crop[0:int(height), 0:int((width/10)*10)]
                    kernel = np.ones((1,1),np.uint8)
                    crop = cv2.erode(crop,kernel,iterations = 1)
                    cv2.imwrite(monFile, crop)

        _monList = myList = ','.join(map(str, monList))
        dbWrapper = DbWrapper(str(args.db_method), str(args.dbip), args.dbport, args.dbusername, args.dbpassword, args.dbname, args.timezone)
        dbWrapper.deleteHashTable(_monList, 'mon')



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
