import time
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
from walkerArgs import parseArgs
from  scanner import Scanner
from threading import Thread, Event
import logging


#from multiprocessing import Process, Queue, Pool
import multiprocessing
#from queue import Queue

log = logging.getLogger()
args = parseArgs()

class RaidScan:
    @staticmethod
    def process(filename):
        curTime = time.time()
        args = parseArgs()
        log.info(filename)
        scanner = Scanner(args.dbip, args.dbport, args.dbusername, args.dbpassword, args.dbname, args.temp_path, args.unknown_path, args.timezone)
        scanner.start_detect(filename, str(curTime))


class checkScreenshot(PatternMatchingEventHandler):
    patterns = ['*.png']
    ignore_directories = True
    ignore_patterns = ""
    case_sensitive = False

    def on_created(self, event):
        log.error("Got new file, appending to queue")
        p = multiprocessing.Process(target=RaidScan.process, args=(event.src_path,))
        p.daemon = True
        p.start()
