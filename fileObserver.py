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

Bounds = collections.namedtuple("Bounds", ['top', 'bottom', 'left', 'right'])



log = logging.getLogger()
args = parseArgs()

class RaidScan:
    @staticmethod
    def process(filename, hash, raidno):
        args = parseArgs()
        scanner = Scanner(args.dbip, args.dbport, args.dbusername, args.dbpassword, args.dbname, args.temp_path, args.unknown_path, args.timezone)
        scanner.start_detect(filename, hash, raidno)


class checkScreenshot(PatternMatchingEventHandler):
    def __init__(self, width, height):
        self.resolutionCalculator = ResolutionCalc(width, height)
        
    patterns = ['*.png']
    ignore_directories = True
    ignore_patterns = ""
    case_sensitive = False
    def on_created(self, event):
        if args.ocr_multitask:
            import multiprocessing
            log.error("Got new file, creating sub-process to process it")
            p = multiprocessing.Process(target=RaidScan.process, args=(event.src_path,))
            p.daemon = True
            p.start()
        else:
            curTime = time.time()
            raidNo = 1
            log.error("Got new file, running ocr scanner")
            raidPic = cv2.imread(event.src_path)
            hash = str(curTime)
            while raidNo < 7:
                raidPicCrop = args.temp_path + "/" + str(hash) + "_raid" + str(raidNo) +".jpg"
                bounds = None
                bounds = self.resolutionCalculator.getRaidBounds(raidNo)
                log.error(bounds)
                raid = raidPic[bounds.top:bounds.bottom, bounds.right:bounds.left]
                cv2.imwrite(raidPicCrop, raid)
                RaidScan.process(raidPicCrop, hash, raidNo)
                raidPic += 1
