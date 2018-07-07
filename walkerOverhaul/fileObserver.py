import time  
from watchdog.observers import Observer  
from watchdog.events import PatternMatchingEventHandler  
from walkerArgs import parseArgs
from  scanner import Scanner
from threading import Thread, Event
import logging

log = logging.getLogger(__name__)
args = parseArgs()

class checkScreenshot(PatternMatchingEventHandler):
    patterns = ['*.jpg']
    
    def process(self, event):
        curTime = time.time()
        # the file will be processed there
        log.info(event.src_path)  # print now only for degug
        scanner = Scanner(args.dbip, args.dbport, args.dbusername, args.dbpassword, args.dbname, args.temp_path, args.unknown_path, args.timezone)
        t_scanner = Thread(scanner.start_detect(event.src_path, str(curTime)),
                           name='scanner')
        t_scanner.daemon = True
        t_scanner.start()
        

    def on_modified(self, event):
        self.process(event)

    def on_created(self, event):
        self.process(event)
         

        

        
         