import time
from datetime import datetime
from threading import Thread, Event
import logging
from colorlog import ColoredFormatter
from walkerArgs import parseArgs
import sys
import os
import math
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
from shutil import copyfile
from copyMons import MonRaidImages
from scanner import Scanner
from fileObserver import checkScreenshot
from routecalc.calculate_route import getJsonRoute, getDistanceOfTwoPointsInMeters
from vnc.vncWrapper import VncWrapper
from telnet.telnetGeo import TelnetGeo
from telnet.telnetMore import TelnetMore
from ocr.pogoWindows import PogoWindows

from ocr.pogoWindows import PogoWindows


class LogFilter(logging.Filter):

    def __init__(self, level):
        self.level = level

    def filter(self, record):
        return record.levelno < self.level

console = logging.StreamHandler()
args = parseArgs()
sleep = False

if not (args.verbose):
    console.setLevel(logging.INFO)

formatter = ColoredFormatter(
    '%(log_color)s [%(asctime)s] [%(threadName)16s] [%(module)14s]' +
    ' [%(levelname)8s] %(message)s',
    datefmt='%m-%d %H:%M:%S',
    reset=True,
    log_colors={
        'DEBUG': 'purple',
        'INFO': 'cyan',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'red,bg_white',
    },
    secondary_log_colors={},
    style='%'
    )

console.setFormatter(formatter)

# Redirect messages lower than WARNING to stdout
stdout_hdlr = logging.StreamHandler(sys.stdout)
stdout_hdlr.setFormatter(formatter)
log_filter = LogFilter(logging.WARNING)
stdout_hdlr.addFilter(log_filter)
stdout_hdlr.setLevel(5)

# Redirect messages equal or higher than WARNING to stderr
stderr_hdlr = logging.StreamHandler(sys.stderr)
stderr_hdlr.setFormatter(formatter)
stderr_hdlr.setLevel(logging.WARNING)

log = logging.getLogger()
log.addHandler(stdout_hdlr)
log.addHandler(stderr_hdlr)

def main():

    sys.excepthook = handle_exception
    args = parseArgs()
    print(args.vnc_ip)
    set_log_and_verbosity(log)
    log.info("Starting TheRaidMap")

    if not os.path.exists(args.raidscreen_path):
        log.info('Raidscreen directory created')
        os.makedirs(args.raidscreen_path)

    MonRaidImages.runAll(args.pogoasset)

    if not args.only_ocr:
        log.info('Starting Scanning Thread....')
        t = Thread(target=main_thread, name='main')
        t.daemon = True
        t.start()

    if not args.only_scan:
        log.info('Starting OCR Thread....')
        t_observ = Thread(name='observer', target=observer(args.raidscreen_path))
        t_observ.daemon = True
        t_observ.start()

    if args.sleeptimer:
        log.info('Starting Sleeptimer....')
        t_sleeptimer = Thread(name='sleeptimer', target=sleeptimer(args.sleepinterval))
        t_sleeptimer.daemon = True
        t_sleeptimer.start()

    while True:
        time.sleep(10)
        #pass
    #loop = asyncio.get_event_loop()
    #tasks = [
    #    asyncio.async(getVNCPic()),
    #    asyncio.async(check_login()),
    #    asyncio.async(check_message()),
    #    asyncio.async(check_Xbutton())]

def sleeptimer(sleeptime):

    while True:
        tmFrom = datetime.strptime(sleeptime[0],"%H:%M")
        tmTil = datetime.strptime(sleeptime[1],"%H:%M")
        tmNow = datetime.strptime(datetime.now().strftime('%H:%M'),"%H:%M")
        global sleep

        if tmNow >= tmFrom and tmNow < tmTil:
            log.info('Going to sleep - byebye')
            #Doing smth over telnet ....
            sleep = True

        while tmNow >= tmFrom and tmNow < tmTil:
            tmNow = datetime.strptime(datetime.now().strftime('%H:%M'),"%H:%M")
            if tmNow >= tmTil:
                log.info('Wakeup - here we go ...')
                #Doing smth over telnet ....
                sleep = False
                break

def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    log.error("Uncaught exception", exc_info=(
        exc_type, exc_value, exc_traceback))

def set_log_and_verbosity(log):
    # Always write to log file.
    args = parseArgs()
    # Create directory for log files.
    if not os.path.exists(args.log_path):
        os.mkdir(args.log_path)
    if not args.no_file_logs:
        filename = os.path.join(args.log_path, args.log_filename)
        filelog = logging.FileHandler(filename)
        filelog.setFormatter(logging.Formatter(
            '%(asctime)s [%(threadName)18s][%(module)14s][%(levelname)8s] ' +
            '%(message)s'))
        log.addHandler(filelog)

    if args.verbose:
            log.setLevel(logging.DEBUG)

            # Let's log some periodic resource usage stats.
            t = Thread(target=log_resource_usage_loop, name='res-usage')
            t.daemon = True
            t.start()
    else:
            log.setLevel(logging.INFO)

def printHi():
    log.error("Finished analyzing screenshot")

def main_thread():
    log.info("Starting VNC client")
    vncWrapper = VncWrapper(str(args.vnc_ip,), 1, args.vnc_port, args.vnc_password)
    log.info("Starting TelnetGeo Client")
    telnGeo = TelnetGeo(str(args.tel_ip), args.tel_port, str(args.tel_password))
    log.info("Starting Telnet MORE Client")
    telnMore = TelnetMore(str(args.tel_ip), args.tel_port, str(args.tel_password))
    log.info("Starting pogo window manager")
    pogoWindowManager = PogoWindows(str(args.vnc_ip,), 1, args.vnc_port, args.vnc_password)



    route = getJsonRoute(args.file)
    lastPogoRestart = time.time()
    print(route)
    #sys.exit(0)
    log.info(args.max_distance)

    while True:
        while sleep:
            time.sleep(1)
        log.info("Next round")
        lastLat = 0.0
        lastLng = 0.0
        curLat = 0.0
        curLng = 0.0
        #TODO:in for loop looping over route:
        #walk to next gym
        #getVNCPic
        #check errors (anything not raidscreen)
        #get to raidscreen (with the above command)
        #take screenshot and store coords in exif with it
        #check time to restart pogo and reset google play services
        for gym in route:
            #gym is an object of format {"lat": "50.583249", "lng": "8.682608"}
            lastLat = curLat
            lastLng = curLng
            log.info(gym)
            curLat = gym['lat']
            curLng = gym['lng']
            #calculate distance inbetween and check for walk vs teleport
            distance = getDistanceOfTwoPointsInMeters(float(lastLat), float(lastLng), float(curLat), float(curLng))
            log.info("Moving to next gym")
            log.info("Distance to cover: %d" % (distance))
            if (args.speed == 0 or
                (args.max_distance and distance > args.max_distance)
                    or (lastLat == 0.0 and lastLng == 0.0)):
                log.info("Teleporting")
                telnGeo.setLocation(curLat, curLng, 0)
                time.sleep(4)
            else:
                log.info("Walking")
                log.info(args.speed)
                telnGeo.walkFromTo(lastLat, lastLng, curLat, curLng, args.speed)
                time.sleep(2)
            #ok, we should be at the next gym, check for errors and stuff
            #TODO: improve errorhandling by checking results and trying again and again
            #not using continue to always take a new screenshot...
            #time.sleep(5)
            vncWrapper.getScreenshot('screenshot.png')
            while (not pogoWindowManager.checkRaidscreen('screenshot.png', 123)):
                #not using continue since we need to get a screen before the next round... TODO: consider getting screen for checkRaidscreen within function
                found =  pogoWindowManager.checkLogin('screenshot.png', 123)
                if not found and pogoWindowManager.checkMessage('screenshot.png', 123):
                    log.error("Message found")
                    found = True
                if not found and pogoWindowManager.checkClosebutton('screenshot.png', 123):
                    log.error("closebutton found")
                    found = True
                if not found and pogoWindowManager.checkSpeedmessage('screenshot.png', 123):
                    log.error("speedmessage found")
                    found = True
                #if pogoWindowManager.checkQuitbutton('screenshot.png', 123):
                #    log.error("Quit message found")
                #    continue
                log.error(not found)
                if not found:
                    pogoWindowManager.checkNearby('screenshot.png', 123)
                #pogoWindowManager.checkNearby('screenshot.png', 123)
                vncWrapper.getScreenshot('screenshot.png')
                #vncWrapper.getScreenshot('screenshot.png')
                #pogoWindowManager.checkQuitbutton('screenshot.png', 123)
                #pogoWindowManager.checkRaidscreen('screenshot.png', 123)
                #vncWrapper.getScreenshot('screenshot.png')

                #TODO: take screenshot of raidscreen?
                #we should now see the raidscreen, let's take a screenshot of it
                time.sleep(1)
            log.info("Saving raid screenshot")
            curTime = time.time()
            copyfile('screenshot.png', args.raidscreen_path + '/Raidscreen' + str(curTime) + '.png')
                ####vncWrapper.getScreenshot('screenshots/nextRaidscreen' + str(curTime) + '.jpg')
                #start_detect()
                #result = pool.apply_async(scanner.start_detect, ['screenshots/nextRaidscreen' + str(time.time()) + '.jpg', 123], printHi) # Evaluate "f(10)" asynchronously calling callback when finished.
                #######scanner.start_detect('screenshots/nextRaidscreen' + str(curTime) + '.jpg', 123)
                #we got the latest raids. To avoid the mobile from killing apps,
                #let's restart pogo every 90minutes or whatever TODO: consider args
                #curTime = time.time()
            if (curTime - lastPogoRestart >= (90 * 60)):
            #time for a restart
                successfulRestart = telnMore.restartApp("com.nianticlabs.pokemongo")
            #TODO: errorhandling if it returned false, maybe try again next round?
                if successfulRestart:
                    lastPogoRestart = curTime
                    time.sleep(25) #just sleep for a couple seconds to have the game come back up again
                #TODO: handle login screen...

def observer(scrPath):
        observer = Observer()
        observer.schedule(checkScreenshot(), path=scrPath)
        observer.start()



if __name__ == '__main__':
    main()
