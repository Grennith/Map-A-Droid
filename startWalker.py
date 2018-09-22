import time
import datetime
from threading import Thread, Event, Lock
import logging
from colorlog import ColoredFormatter
from walkerArgs import parseArgs
import sys
import glob, os
import math
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
from shutil import copyfile
from copyMons import MonRaidImages
from fileObserver import checkScreenshot
import heapq
from multiprocessing import Process

from routecalc.calculate_route import getJsonRoute, getDistanceOfTwoPointsInMeters
from telnet.telnetGeo import TelnetGeo
from telnet.telnetMore import TelnetMore
from db.dbWrapper import DbWrapper
from screenWrapper import ScreenWrapper
from ocr.pogoWindows import PogoWindows
from checkWeather import checkWeather
import collections

import cv2
from PIL import Image

RaidLocation = collections.namedtuple('RaidLocation', ['latitude', 'longitude'])


class LogFilter(logging.Filter):

    def __init__(self, level):
        self.level = level

    def filter(self, record):
        return record.levelno < self.level

console = logging.StreamHandler()
args = parseArgs()
sleep = False
nextRaidQueue = []

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

telnMore = None
pogoWindowManager = None
screenWrapper = None
runWarningThreadEvent = Event()
windowLock = Lock()
lastScreenshotTaken = 0
lastPogoRestart = None
lastScreenHash = '0'
lastScreenHashCount = 0

redErrorCount = 0

dbWrapper = DbWrapper(str(args.db_method), str(args.dbip), args.dbport, args.dbusername, args.dbpassword, args.dbname,
                      args.timezone)

if not args.only_ocr:
    log.info("Starting Telnet MORE Client")
    telnMore = TelnetMore(str(args.tel_ip), args.tel_port, str(args.tel_password), args.tel_timeout_command,
                          args.tel_timeout_socket)
    log.info("Starting ScreenWrapper")
    screenWrapper = ScreenWrapper(args.screen_method, telnMore, str(args.vnc_ip), args.vnc_port, args.vnc_password,
                                  args.vncscreen)

    log.info("Starting pogo window manager")
    pogoWindowManager = PogoWindows(screenWrapper, args.screen_width, args.screen_height, args.temp_path)


def main():
    global dbWrapper
    log.info("Starting TheRaidMap")
    sys.excepthook = handle_exception
    log.info("Parsing arguments")
    args = parseArgs()
    set_log_and_verbosity(log)

    dbWrapper.createHashDatabaseIfNotExists()

    if args.clean_hash_database:
        log.info('Cleanup Hash Database and www_hash folder')
        dbWrapper.deleteHashTable('999', '')
        for file in glob.glob("www_hash/*.jpg"):
            os.remove(file)
        sys.exit(0)

    if not os.path.exists(args.raidscreen_path):
        log.info('Raidscreen directory created')
        os.makedirs(args.raidscreen_path)

    MonRaidImages.runAll(args.pogoasset)

    if not args.only_ocr:
        log.info('Processing Pokemon Matching....')
        t = Thread(target=main_thread, name='main')
        t.daemon = True
        t.start()

    if not args.only_scan:
        if not dbWrapper.ensureLastUpdatedColumn():
            log.fatal("Missing raids.last_updated column and couldn't create it")
            sys.exit(1)

        dbWrapper.createHashDatabaseIfNotExists()

        log.info('Starting OCR Thread....')
        t_observ = Thread(name='observer', target=observer(args.raidscreen_path, args.screen_width, args.screen_height))
        t_observ.daemon = True
        t_observ.start()

        log.info('Starting Cleanup Thread....')
        t_observ = Thread(name='cleanupraidscreen',
                          target=deleteOldScreens(args.raidscreen_path, args.successsave_path, args.cleanup_age))
        t_observ.daemon = True
        t_observ.start()

    if args.sleeptimer:
        log.info('Starting Sleeptimer....')
        t_sleeptimer = Thread(name='sleeptimer',
                              target=sleeptimer)
        t_sleeptimer.daemon = True
        t_sleeptimer.start()

    if args.auto_hatch:
        log.info('Starting Auto Hatch....')
        t_auto_hatch = Thread(name='level_5_auto_hatch', target=level_5_auto_hatch)
        t_auto_hatch.daemon = True
        t_auto_hatch.start()

    while True:
        time.sleep(10)


def level_5_auto_hatch():
    while sleep is not True and args.auto_hatch:
        dbWrapper.autoHatchEggs()
        log.debug("auto_hatch going to sleep for 60 seconds")
        time.sleep(60)
        log.debug("Sleep Status: " + str(sleep))
        log.debug("Auto Hatch Enabled: " + str(args.auto_hatch))


def deleteOldScreens(folderscreen, foldersuccess, minutes):
    if minutes == "0":
        log.info('deleteOldScreens: Search/Delete Screenshots is disabled')
        return

    while True:
        log.info('deleteOldScreens: Search/Delete Screenshots older than ' + str(minutes) + ' minutes')

        now = time.time()
        only_files = []

        log.debug('deleteOldScreens: Cleanup Folder: ' + str(folderscreen))
        for file in os.listdir(folderscreen):
            file_full_path = os.path.join(folderscreen, file)
            if os.path.isfile(file_full_path) and file.endswith(".png"):
                # Delete files older than x days
                if os.stat(file_full_path).st_mtime < now - int(minutes) * 60:
                    os.remove(file_full_path)
                    log.debug('deleteOldScreens: File Removed : ' + file_full_path)

        if args.save_success:

            if not os.path.exists(args.successsave_path):
                log.info('deleteOldScreens: Save directory created')
                os.makedirs(args.successsave_path)

            log.debug('deleteOldScreens: Cleanup Folder: ' + str(foldersuccess))
            for file in os.listdir(foldersuccess):
                file_full_path = os.path.join(foldersuccess, file)
                if os.path.isfile(file_full_path) and file.endswith(".jpg"):
                    # Delete files older than x days
                    if os.stat(file_full_path).st_mtime < now - int(minutes) * 60:
                        os.remove(file_full_path)
                        log.debug('deleteOldScreens: File Removed : ' + file_full_path)

        log.info('deleteOldScreens: Search/Delete Screenshots finished')
        time.sleep(3600)


def sleeptimer():
    sleeptime = args.sleepinterval
    global sleep
    global telnMore
    tmFrom = datetime.datetime.strptime(sleeptime[0], "%H:%M")
    log.debug("sleeptimer: tmFrom: %s" % str(tmFrom))
    tmTil = datetime.datetime.strptime(sleeptime[1], "%H:%M") + datetime.timedelta(hours=24)
    log.debug("sleeptimer: tmTil: %s" % str(tmTil))
    while True:
        # we assume sleep is always at night...
        tmNow = datetime.datetime.strptime(datetime.datetime.now().strftime('%H:%M'), "%H:%M")
        tmNowNextDay = tmNow + datetime.timedelta(hours=24)
        log.debug("Time now: %s" % tmNow)
        log.debug("Time Now Next Day: %s" % tmNowNextDay)
        log.debug("Time From: %s" % tmFrom)
        log.debug("Time Til: %s" % tmTil)

        if tmNow >= tmFrom or tmNowNextDay < tmTil:
            log.info('Going to sleep - bye bye')
            # Stopping pogo...
            if telnMore:
                telnMore.stopApp("com.nianticlabs.pokemongo")
                telnMore.clearAppCache("com.nianticlabs.pokemongo")
            sleep = True

            while sleep:
                log.info("Currently sleeping...zzz")
                log.debug("Time now: %s" % tmNow)
                log.debug("Time Now Next Day: %s" % tmNowNextDay)
                log.debug("Time From: %s" % tmFrom)
                log.debug("Time Til: %s" % tmTil)
                tmNow = datetime.datetime.strptime(datetime.datetime.now().strftime('%H:%M'), "%H:%M")
                tmNowNextDay = tmNow + datetime.timedelta(hours=24)
                log.info('Still sleeping, current time... %s' % str(tmNow))
                if tmNowNextDay >= tmTil and tmNow < tmFrom:
                    log.debug("Time now: %s" % tmNow)
                    log.debug("Time Now Next Day: %s" % tmNowNextDay)
                    log.debug("Time From: %s" % tmFrom)
                    log.debug("Time Til: %s" % tmTil)

                    log.warning('sleeptimer: Wakeup - here we go ...')
                    # Turning screen on and starting app
                    if telnMore:
                        telnMore.turnScreenOn()
                        telnMore.startApp("sleeptimer: com.nianticlabs.pokemongo")
                    sleep = False
                    break
                time.sleep(300)
        time.sleep(300)


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
    else:
        log.setLevel(logging.INFO)


# to be called regularly... like every 5mins? no idea... would be nicer to simply insert updates
def updateRaidQueue(dbWrapper):
    log.info("Updating raid queue")
    newQueue = dbWrapper.getNextRaidHatches(args.delay_after_hatch)
    log.debug("New raid queue: %s" % str(newQueue))
    mergeRaidQueue(newQueue)
    # heapq.heapify(newQueue)


def mergeRaidQueue(newQueue):
    global nextRaidQueue
    merged = list(set(newQueue + nextRaidQueue))
    heapq.heapify(merged)
    nextRaidQueue = merged
    log.info("New raidqueue: %s" % nextRaidQueue)


def restartPogo():
    global redErrorCount
    curTime = time.time()
    successfulStop = stopPogo()
    # TODO: errorhandling if it returned false, maybe try again next round?
    # TODO: check if pogo was closed...
    log.debug("restartPogo: stop pogo resulted in %s" % str(successfulStop))
    redErrorCount = 0
    if successfulStop:
        telnMore.clearAppCache("com.nianticlabs.pokemongo")
        time.sleep(1)
        return startPogo()
        # TODO: handle login screen... ?
    else:
        return False


def tabOutAndInPogo():
    global telnMore
    telnMore.startApp("de.grennith.rgc.remotegpscontroller")
    time.sleep(7)
    telnMore.startApp("com.nianticlabs.pokemongo")
    time.sleep(2)


def stopPogo():
    global telnMore
    stopResult = telnMore.stopApp("com.nianticlabs.pokemongo")
    pogoTopmost = telnMore.isPogoTopmost()
    while pogoTopmost:
        stopResult = telnMore.stopApp("com.nianticlabs.pokemongo")
        time.sleep(1)
        pogoTopmost = telnMore.isPogoTopmost()
    return stopResult


def startPogo():
    global telnMore
    global lastPogoRestart
    pogoTopmost = telnMore.isPogoTopmost()
    if pogoTopmost:
        return True

    curTime = time.time()
    startResult = False
    while not pogoTopmost:
        startResult = telnMore.startApp("com.nianticlabs.pokemongo")
        time.sleep(1)
        pogoTopmost = telnMore.isPogoTopmost()
    reachedRaidtab = False
    if startResult:
        log.warning("startPogo: Starting pogo...")
        time.sleep(args.post_pogo_start_delay)
        lastPogoRestart = curTime

        # let's handle the login and stuff
        reachedRaidtab = getToRaidscreen(15, True)

    return reachedRaidtab


def getToRaidscreen(maxAttempts, again=False):
    # check for any popups (including post login OK)
    global lastScreenshotTaken
    global redErrorCount

    log.debug("getToRaidscreen: Trying to get to the raidscreen with %s max attempts..." % str(maxAttempts))
    pogoTopmost = telnMore.isPogoTopmost()
    if not pogoTopmost:
        return False

    checkPogoFreeze()
    if not takeScreenshot(delayBefore=args.post_screenshot_delay):
        if again:
            log.error("getToRaidscreen: failed getting a screenshot again")
        getToRaidscreen(maxAttempts, True)

    attempts = 0

    if os.path.isdir(os.path.join(args.temp_path, 'screenshot.png')):
        log.error("getToRaidscreen: screenshot.png is not a file/corrupted")
        return False
    
    while pogoWindowManager.isGpsSignalLost(os.path.join(args.temp_path, 'screenshot.png'), 123):
        time.sleep(1)
        takeScreenshot()
        log.warning("getToRaidscreen: GPS signal error")
        redErrorCount += 1
        if redErrorCount > 3:
            log.error("getToRaidscreen: Red error multiple times in a row, restarting")
            redErrorCount = 0
            restartPogo()
            return False
    redErrorCount = 0

    while not pogoWindowManager.checkRaidscreen(os.path.join(args.temp_path, 'screenshot.png'), 123):
        if attempts > maxAttempts:
            # could not reach raidtab in given maxAttempts
            log.error("getToRaidscreen: Could not get to raidtab within %s attempts" % str(maxAttempts))
            return False
        checkPogoFreeze()
        # not using continue since we need to get a screen before the next round...
        found = pogoWindowManager.lookForButton(os.path.join(args.temp_path, 'screenshot.png'), 2.20, 3.01)
        if found:
            log.info("getToRaidscreen: Found button (small)")

        if not found and pogoWindowManager.checkCloseExceptNearbyButton(os.path.join(args.temp_path, 'screenshot.png'), 123):
            log.info("getToRaidscreen: Found (X) button (except nearby)")
            found = True

        if not found and pogoWindowManager.lookForButton(os.path.join(args.temp_path, 'screenshot.png'), 1.05, 2.20):
            log.info("getToRaidscreen: Found button (big)")
            found = True

        log.info("getToRaidscreen: Previous checks found popups: %s" % str(found))
        if not found:
            log.info("getToRaidscreen: Previous checks found nothing. Checking nearby open")
            if pogoWindowManager.checkNearby(os.path.join(args.temp_path, 'screenshot.png'), 123):
                return takeScreenshot(delayBefore=args.post_screenshot_delay)

        if not takeScreenshot(delayBefore=args.post_screenshot_delay):
            return False

        attempts += 1

    log.debug("getToRaidscreen: done")
    return True


def turnScreenOnAndStartPogo():
    global telnMore
    if not telnMore.isScreenOn():
        telnMore.startApp("de.grennith.rgc.remotegpscontroller")
        log.warning("Turning screen on")
        telnMore.turnScreenOn()
        time.sleep(args.post_turn_screen_on_delay)
    # check if pogo is running and start it if necessary
    log.warning("turnScreenOnAndStartPogo: (Re-)Starting Pogo")
    restartPogo()


def reopenRaidTab():
    global pogoWindowManager
    log.info("reopenRaidTab: Attempting to retrieve screenshot before checking raidtab")
    if not takeScreenshot():
        log.error("reopenRaidTab: Failed retrieving screenshot before checking for closebutton")
        return
    pogoWindowManager.checkCloseExceptNearbyButton(os.path.join(args.temp_path, 'screenshot.png'), '123', 'True')
    getToRaidscreen(3)
    time.sleep(1)


def takeScreenshot(delayAfter=0.0, delayBefore=0.0):
    global lastScreenshotTaken
    time.sleep(delayBefore)
    compareToTime = time.time() - lastScreenshotTaken
    if lastScreenshotTaken and compareToTime < 0.5:
        log.debug("takeScreenshot: screenshot taken recently, returning immediately")
        return True
    elif not screenWrapper.getScreenshot(os.path.join(args.temp_path, 'screenshot.png')):
        log.error("takeScreenshot: Failed retrieving screenshot")
        return False
    else:
        lastScreenshotTaken = time.time()
        time.sleep(delayAfter)
        return True


def checkPogoFreeze():
    global lastScreenHash
    global lastScreenHashCount

    if not takeScreenshot():
        return
    
    screenHash = getImageHash(os.path.join(args.temp_path, 'screenshot.png'))
    log.debug("checkPogoFreeze: Old Hash: " + lastScreenHash)
    log.debug("checkPogoFreeze: New Hash: " + screenHash)
    if hamming_distance(str(lastScreenHash), str(screenHash)) < 4 and lastScreenHash != '0':
        log.debug("checkPogoFreeze: New und old Screenshoot are the same - no processing")
        lastScreenHashCount += 1
        log.debug("checkPogoFreeze: Same Screen Count: " + str(lastScreenHashCount))
        if lastScreenHashCount >= 100:
            lastScreenHashCount = 0
            restartPogo()
    else:
        lastScreenHash = screenHash
        lastScreenHashCount = 0


# supposed to be running mostly in the post walk/teleport delays...
def checkSpeedWeatherWarningThread():
    global sleep
    global runWarningThreadEvent
    global windowLock
    global telnMore
    while True:
        while sleep:
            time.sleep(0.5)
        log.debug("checkSpeedWeatherWarningThread: acquiring lock")
        windowLock.acquire()
        log.debug("checkSpeedWeatherWarningThread: lock acquired")

        log.debug("checkSpeedWeatherWarningThread: Checking if pogo is running...")
        if not telnMore.isPogoTopmost():
            log.warning("checkSpeedWeatherWarningThread: Starting Pogo")
            restartPogo()

        reachedRaidscreen = getToRaidscreen(10, True)
        if reachedRaidscreen:
            log.debug("checkSpeedWeatherWarningThread: checkSpeedWeatherWarningThread: reached raidscreen...")
            runWarningThreadEvent.set()
        else:
            log.debug("checkSpeedWeatherWarningThread: did not reach raidscreen in 10 attempts")
            runWarningThreadEvent.clear()
        log.debug("checkSpeedWeatherWarningThread: releasing lock")
        windowLock.release()
        time.sleep(1)


def main_thread():
    global nextRaidQueue
    global lastPogoRestart
    global telnMore
    global pogoWindowManager
    global sleep
    global runWarningThreadEvent
    global windowLock
    global screenWrapper
    global lastScreenshotTaken
    global lastScreenHash
    global lastScreenHashCount

    log.info("main: Starting TelnetGeo Client")
    telnGeo = TelnetGeo(str(args.tel_ip), args.tel_port, str(args.tel_password), args.tel_timeout_command,
                        args.tel_timeout_socket)

    log.info("main: Starting dbWrapper")
    dbWrapper = DbWrapper(str(args.db_method), str(args.dbip), args.dbport, args.dbusername, args.dbpassword,
                          args.dbname, args.timezone)
    updateRaidQueue(dbWrapper)
    lastRaidQueueUpdate = time.time()

    if lastPogoRestart is None:
        lastPogoRestart = time.time()

    route = getJsonRoute(args.file, args.gym_distance, args.max_count_gym_sum_up_around_gym, args.route_file)

    log.info("main: Route to be taken: %s, amount of coords: %s" % (str(route), str(len(route))))
    log.info("main: Max_distance before teleporting: %s" % args.max_distance)
    log.info("main: Checking if screen is on and pogo is running")

    if not sleep:
        if args.no_initial_restart is False:
            turnScreenOnAndStartPogo()
        else:
            startPogo()

    log.info('Starting speedweatherWarning Thread....')
    w = Thread(target=checkSpeedWeatherWarningThread, name='speedWeatherCheck')
    w.daemon = True
    w.start()

    emptycount = 0
    locationCount = 0
    while True:
        log.info("main: Next round")
        curLat = 0.0
        curLng = 0.0
        i = 0  # index in route
        failcount = 0
        lastRoundEggHatch = False

        # loop over gyms:
        # walk to next gym
        # get to raidscreen
        # take screenshot
        # check time to restart pogo

        # process the entire route, prioritize hatched eggs in every second round (if anything has hatched)
        while i < len(route):
            while sleep:
                time.sleep(1)
            curTime = time.time()
            # update the raid queue every 5mins...
            if (curTime - lastRaidQueueUpdate) >= (5 * 60):
                updateRaidQueue(dbWrapper)
                lastRaidQueueUpdate = curTime

            windowLock.acquire()
            # Restart pogo every now and then...
            if args.restart_pogo > 0:
                # log.debug("main: Current time - lastPogoRestart: %s" % str(curTime - lastPogoRestart))
                # if curTime - lastPogoRestart >= (args.restart_pogo * 60):
                locationCount += 1
                if locationCount > args.restart_pogo:
                    log.error("scanned " + str(args.restart_pogo) + " locations, restarting pogo")
                    restartPogo()
                    locationCount = 0
            windowLock.release()

            # let's check for speed and weather warnings while we're walking/teleporting...
            runWarningThreadEvent.set()
            lastLat = curLat
            lastLng = curLng
            egghatchLocation = False
            log.debug("main: Checking for raidqueue priority. Current time: %s, Current queue: %s" % (
                str(time.time()), str(nextRaidQueue)))
            # determine whether we move to the next gym or to the top of our priority queue
            if not lastRoundEggHatch and len(nextRaidQueue) > 0 and nextRaidQueue[0][0] < time.time():
                # the topmost item in the queue lays in the past...
                log.info('main: An egg has hatched, get there asap. Location: %s' % str(nextRaidQueue[0]))
                egghatchLocation = True
                nextStop = heapq.heappop(nextRaidQueue)[1]  # gets the location tuple
                curLat = nextStop.latitude
                curLng = nextStop.longitude
                time.sleep(1)
                lastRoundEggHatch = True
            else:
                # continue as usual
                log.info('main: Moving on with gym at %s' % route[i])
                curLat = route[i]['lat']
                curLng = route[i]['lng']
                # remove whitespaces that might be on either side...
                i += 1
                lastRoundEggHatch = False

            # store current position in file
            posfile = open(args.position_file+'.position', "w")
            posfile.write(str(curLat)+", "+str(curLng))
            posfile.close()

            log.debug("main: next stop: %s, %s" % (str(curLat), str(curLng)))
            log.debug('main: LastLat: %s, LastLng: %s, CurLat: %s, CurLng: %s' % (lastLat, lastLng, curLat, curLng))
            # get the distance from our current position (last) to the next gym (cur)
            distance = getDistanceOfTwoPointsInMeters(float(lastLat), float(lastLng), float(curLat), float(curLng))
            log.info('main: Moving %s meters to the next position' % distance)
            delayUsed = 0
            if (args.speed == 0 or
                    (args.max_distance and 0 < args.max_distance < distance)
                    or (lastLat == 0.0 and lastLng == 0.0)):
                log.info("main: Teleporting...")
                telnGeo.setLocation(curLat, curLng, 0)
                delayUsed = args.post_teleport_delay
                # Test for cooldown / teleported distance
                if args.cool_down_sleep:
                    if distance > 2500:
                        delayUsed = 30
                    elif distance > 5000:
                        delayUsed = 45
                    elif distance > 10000:
                        delayUsed = 60

                if 0 < args.walk_after_teleport_distance < distance:
                    toWalk = getDistanceOfTwoPointsInMeters(float(curLat), float(curLng), float(curLat) + 0.0001, float(curLng) + 0.0001)
                    log.error("Walking a bit: %s" % str(toWalk))
                    time.sleep(0.3)
                    telnGeo.walkFromTo(curLat, curLng, curLat + 0.0001, curLng + 0.0001, 11)
                    log.error("Walking back")
                    time.sleep(0.3)
                    telnGeo.walkFromTo(curLat + 0.0001, curLng + 0.0001, curLat, curLng, 11)
                    log.error("Done walking")
            else:
                log.info("main: Walking...")
                telnGeo.walkFromTo(lastLat, lastLng, curLat, curLng, args.speed)
                delayUsed = args.post_walk_delay
            time.sleep(delayUsed)

            # ok, we should be at the next gym, check for errors and stuff
            # TODO: improve errorhandling by checking results and trying again and again
            # not using continue to always take a new screenshot...
            log.debug("main: Acquiring lock")

            while sleep or not runWarningThreadEvent.isSet():
                time.sleep(0.1)
            windowLock.acquire()
            log.debug("main: Lock acquired")
            if not takeScreenshot():
                windowLock.release()
                continue

            if args.last_scanned:
                log.info('main: Set new scannedlocation in Database')
                dbWrapper.setScannedLocation(str(curLat), str(curLng), str(curTime))

            log.info("main: Checking raidcount and copying raidscreen if raids present")
            countOfRaids = pogoWindowManager.readRaidCircles(os.path.join(args.temp_path, 'screenshot.png'), 123)
            if countOfRaids == -1:
                # reopen raidtab and take screenshot...
                log.warning("main: Count present but no raid shown, reopening raidTab")
                reopenRaidTab()
                # tabOutAndInPogo()
                if not takeScreenshot():
                    windowLock.release()
                    continue
                countOfRaids = pogoWindowManager.readRaidCircles(os.path.join(args.temp_path, 'screenshot.png'), 123)
            #    elif countOfRaids == 0:
            #        emptycount += 1
            #        if emptycount > 30:
            #            emptycount = 0
            #            log.error("Had 30 empty scans, restarting pogo")
            #            restartPogo()

            # not an elif since we may have gotten a new screenshot..
            #detectin weather
            if args.weather:
                weather = checkWeather(os.path.join(args.temp_path, 'screenshot.png'))
                if weather[0]:
                    log.debug('Submit Weather')
                    dbWrapper.updateInsertWeather(curLat, curLng, weather[1], curTime)
                else:
                    log.error('Weather could not detected')
            
            
            if countOfRaids > 0:
                log.debug("main: New und old Screenshoot are different - starting OCR")
                log.debug("main: countOfRaids: %s" % str(countOfRaids))
                curTime = time.time()
                copyFileName = args.raidscreen_path + '/raidscreen_' + str(curTime) + "_" + str(curLat) + "_" + str(
                    curLng) + "_" + str(countOfRaids) + '.png'
                log.debug('Copying file: ' + copyFileName)
                copyfile(os.path.join(args.temp_path, 'screenshot.png'), copyFileName)
                os.remove(os.path.join(args.temp_path, 'screenshot.png'))

            log.debug("main: Releasing lock")
            windowLock.release()


def dhash(image, hash_size=8):
    # Grayscale and shrink the image in one step.
    image = image.convert('L').resize(
        (hash_size + 1, hash_size),
        Image.ANTIALIAS,
    )
    pixels = list(image.getdata())
    # Compare adjacent pixels.
    difference = []
    for row in xrange(hash_size):
        for col in xrange(hash_size):
            pixel_left = image.getpixel((col, row))
            pixel_right = image.getpixel((col + 1, row))
            difference.append(pixel_left > pixel_right)
        # Convert the binary array to a hexadecimal string.
        decimal_value = 0
        hex_string = []
        for index, value in enumerate(difference):
            if value:
                decimal_value += 2 ** (index % 8)
            if (index % 8) == 7:
                hex_string.append(hex(decimal_value)[2:].rjust(2, '0'))
                decimal_value = 0
    hashValue = ''.join(hex_string)
    return hashValue


def getImageHash(image, hashSize=8):
    time.sleep(2)
    try:
        image_temp = cv2.imread(image)
    except Exception as e:
        log.error("Screenshot corrupted :(")
        log.debug(e)
        return '0'
    if image_temp is None:
        log.error("Screenshot corrupted :(")
        return '0'

    hashPic = Image.open(image)
    imageHash = dhash(hashPic, hashSize)
    return imageHash


def hamming_distance(str1, str2):
    diffs = 0
    for ch1, ch2 in zip(str1, str2):
        if ch1 != ch2:
            diffs += 1
    return diffs


def observer(scrPath, width, height):
    observer = Observer()
    observer.schedule(checkScreenshot(width, height), path=scrPath)
    observer.start()


if __name__ == '__main__':
    main()
