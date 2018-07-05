import cv2
import os
import numpy as np
import imutils
import os
import os.path
import logging
from utils import get_args

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
        raidMons = ["68", "142", "90", "378", "382", "125", "303", "129", "359", "248", "95", "185", "306", "76", "112", "310", "138", "140", "320", '135', '185']

        if not os.path.exists(assetPath):
            log.error('PogoAssets not found')
            exit(0)

        for mon in raidMons:

            mon = '{:03d}'.format(int(mon))
            monFile = monImgPath + '_mon_' + str(mon) + '_.png'

            if not os.path.isfile(monFile):

                log.info('Processing Pokedex Nr: ' + str(mon))

                monFileAsset = assetPath + 'decrypted_assets/pokemon_icon_' + str(mon) + '_00.png'

                if not os.path.isfile(monFileAsset):
                    log.error('File ' + str(monFileAsset) + ' not found')
                    exit(0)


                MonRaidImages.read_transparent_png(monFileAsset, monFile)

                monAsset = cv2.imread(monFile,3)
                height, width, channels = monAsset.shape
                monAsset = cv2.inRange(monAsset,np.array([255,255,255]),np.array([255,255,255]))
                cv2.imwrite(monFile, monAsset)
                crop = cv2.imread(monFile,3)
                crop = crop[0:int(height), 0:int((width/6)*4)]
                cv2.imwrite(monFile, crop)
                log.info('Processing Pokemon Nr: ' + str(mon) + ' finished')

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
