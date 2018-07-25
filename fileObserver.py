import time
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
from walkerArgs import parseArgs
from  segscanner import Scanner
from threading import Thread, Event
import logging
from ocr.resolutionCalculator import *
import collections
import cv2
import multiprocessing
#from ocr.pogoWindows import PogoWindows
import re


Bounds = collections.namedtuple("Bounds", ['top', 'bottom', 'left', 'right'])



log = logging.getLogger()
args = parseArgs()

class RaidScan:
    @staticmethod
    def process(filename, hash, raidno):
        args = parseArgs()
        scanner = Scanner(args.dbip, args.dbport, args.dbusername, args.dbpassword, args.dbname, args.temp_path, args.unknown_path, args.timezone)
        checkcrop = scanner.start_detect(filename, hash, raidno)
        return checkcrop

class checkScreenshot(PatternMatchingEventHandler):
    def __init__(self, width, height):
        self.resolutionCalculator = ResolutionCalc(width, height)
        log.info("Starting pogo window manager in OCR thread")
        #self.pogoWindowManager = PogoWindows(str(args.vnc_ip,), 1, args.vnc_port, args.vnc_password, args.screen_width, args.screen_height, args.temp_path)

        #self.procPool = Pool(10)

    def prepareAnalysis(self, raidNo, bounds, screenshot):
        curTime = time.time()
        hash = str(curTime)
        raidCropFilepath = args.temp_path + "/" + str(hash) + "_raidcrop" + str(raidNo) + ".jpg"
        log.debug("dispatchAnalysis: Scanning bounds %s" % str(bounds))
        raidCrop = screenshot[bounds.top : bounds.bottom, bounds.left : bounds.right]
        cv2.imwrite(raidCropFilepath, raidCrop)
        p = None
        if args.ocr_multitask:
            p = multiprocessing.Process(target=RaidScan.process, name='OCR-crop-analysis-' + str(raidNo), args=(raidCropFilepath, hash, raidNo,))
        else:
            p = Thread(target=RaidScan.process, name='OCR-processing', args=(raidCropFilepath, hash, raidNo,))
        return p

    def process(self, event):
        #pathSplit = event.src_path.split("/")
        #filename = pathSplit[len(pathSplit) - 1]
        #print filename
        raidcount = re.search('.*_(\d*)\.png', event.src_path)
        if raidcount is None:
            #we could not read the raidcount... stop
            log.warning("Could not read raidcount in %s" % event.src_path)
            return
        amountOfRaids = int(raidcount.group(1))
        log.debug("Read a raidcount of %s in new file" % str(amountOfRaids))
        raidPic = cv2.imread(event.src_path)
        #amountOfRaids = self.pogoWindowManager.getAmountOfRaids(event.src_path)
        if amountOfRaids is None or amountOfRaids == 0:
            return
        log.debug(amountOfRaids)    
        log.debug('weiter')
        processes = []
        bounds = []

        if int(amountOfRaids) == 1:
            #we got just one raid...
            boundsOfSingleRaid = self.resolutionCalculator.getRaidBoundsSingle()
            log.debug(boundsOfSingleRaid)
            log.debug('hiersindwir')
            p = self.prepareAnalysis(1, boundsOfSingleRaid, raidPic)
            processes.append(p)
            p.daemon = True
            p.start()
        elif amountOfRaids == 2:
            bounds.append(self.resolutionCalculator.getRaidBoundsTwo(1))
            bounds.append(self.resolutionCalculator.getRaidBoundsTwo(2))
        else:
            if amountOfRaids is None or amountOfRaids > 6:
                amountOfRaids = 6 #ignore any more raids, shouldn't be the case all too often
            for i in range(amountOfRaids): #0 to 5....
                bounds.append(self.resolutionCalculator.getRaidBounds(i + 1))
        log.debug('weiter')
        log.debug(bounds)
        for i in range(len(bounds)):
            p = self.prepareAnalysis(i + 1, bounds[i], raidPic)
            processes.append(p)
            p.daemon = True
            p.start()

        #TODO: join threads/processes
        log.debug("process: Done starting off processes")

    patterns = ['*.png']
    ignore_directories = True
    ignore_patterns = ""
    case_sensitive = False
    def on_created(self, event):
        t = Thread(target=self.process(event), name='OCR-processing')
        t.daemon = True
        t.start()
        #TODO: code this better....
