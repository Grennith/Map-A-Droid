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
        #self.procPool = Pool(10)

    def process(self, event):
        if args.ocr_multitask:
            import multiprocessing
            raidNo = 1
            raidPic = cv2.imread(event.src_path)
            log.info("Got new file, running ocr scanner with processes")
            processes = []
            while raidNo < 7:
                curTime = time.time()
                hash = str(curTime)
                raidPicCrop = args.temp_path + "/" + str(hash) + "_raidcrop" + str(raidNo) +".jpg"
                bounds = None
                bounds = self.resolutionCalculator.getRaidBounds(raidNo)
                log.debug("on_created: scanning bounds: %s of %s" % (str(bounds), str(event.src_path)))
                raid = raidPic[bounds.top:bounds.bottom, bounds.left:bounds.right]
                cv2.imwrite(raidPicCrop, raid)
                p = multiprocessing.Process(target=RaidScan.process, name='OCR-Process', args=(raidPicCrop, hash, raidNo,))
                processes.append(p)
                p.daemon = True
                p.start()
                raidNo += 1

            log.info("Finished starting off processes")
            #for process in processes:
                #process.join()
            log.info("Done with new screenshot")
        else:
            raidNo = 1
            raidPic = cv2.imread(event.src_path)
            log.error("Got new file, running ocr scanner as normal thread")
            while raidNo < 7:
                curTime = time.time()
                hash = str(curTime)
                raidPicCrop = args.temp_path + "/" + str(hash) + "_raidcrop" + str(raidNo) +".jpg"
                bounds = None
                bounds = self.resolutionCalculator.getRaidBounds(raidNo)
                log.debug("on_created: scanning bounds: %s of %s" % (str(bounds), str(event.src_path)))
                raid = raidPic[bounds.top:bounds.bottom, bounds.left:bounds.right]
                cv2.imwrite(raidPicCrop, raid)
                checkcrop = RaidScan.process(raidPicCrop, hash, raidNo)
                if not checkcrop:
                    break
                raidNo += 1

    patterns = ['*.png']
    ignore_directories = True
    ignore_patterns = ""
    case_sensitive = False
    def on_created(self, event):
        t = Thread(target=self.process(event), name='OCR-processing')
        t.daemon = True
        t.start()
        #TODO: code this better....
