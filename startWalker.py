import time
from datetime import datetime
from threading import Thread, Event, Lock
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
from fileObserver import checkScreenshot
import heapq
from multiprocessing import Process

from routecalc.calculate_route import getJsonRoute, getDistanceOfTwoPointsInMeters
from telnet.telnetGeo import TelnetGeo
from telnet.telnetMore import TelnetMore
from dbWrapper import *
from screenWrapper import ScreenWrapper
from ocr.pogoWindows import PogoWindows
import collections


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
screenWrapper =  None
runWarningThreadEvent = Event()
windowLock = Lock()
lastScreenshotTaken = 0
lastPogoRestart = None
if not args.only_ocr:
    log.info("Starting Telnet MORE Client")
    telnMore = TelnetMore(str(args.tel_ip), args.tel_port, str(args.tel_password))
    log.info("Starting ScreenWrapper")
    screenWrapper = ScreenWrapper(args.screen_method, telnMore, str(args.vnc_ip), args.vnc_port, args.vnc_password, args.vncscreen)

    log.info("Starting pogo window manager")
    pogoWindowManager = PogoWindows(screenWrapper, args.screen_width, args.screen_height, args.temp_path)


def main():
    log.info("Starting TheRaidMap")
    sys.excepthook = handle_exception
    log.info("Parsing arguments")
    args = parseArgs()
    set_log_and_verbosity(log)
    dbWrapper = DbWrapper(str(args.dbip), args.dbport, args.dbusername, args.dbpassword, args.dbname, args.timezone)

    if args.clean_hash_database:
        log.info('Cleanup Hash Database')
        dbWrapper.deleteHashTable('999', '')

    if not os.path.exists(args.raidscreen_path):
        log.info('Raidscreen directory created')
        os.makedirs(args.raidscreen_path)


    dbWrapper.createHashDatabaseIfNotExists()

    MonRaidImages.runAll(args.pogoasset)

    if not args.only_ocr:
        log.info('Starting Scanning Thread....')
        t = Thread(target=main_thread, name='main')
        t.daemon = True
        t.start()
        log.info('Starting speedweatherWarning Thread....')
        w = Thread(target=checkSpeedWeatherWarningThread, name='speedWeatherCheck')
        w.daemon = True
        w.start()

    if not args.only_scan:
        log.info('Starting OCR Thread....')
        t_observ = Thread(name='observer', target=observer(args.raidscreen_path, args.screen_width, args.screen_height))
        t_observ.daemon = True
        t_observ.start()

        log.info('Starting Cleanup Thread....')
        t_observ = Thread(name='cleanupraidscreen', target=deleteOldScreens(args.raidscreen_path, args.successsave_path, args.cleanup_age))
        t_observ.daemon = True
        t_observ.start()

    if args.sleeptimer:
        log.info('Starting Sleeptimer....')
        t_sleeptimer = Thread(name='sleeptimer', target=sleeptimer(args.sleepinterval))
        t_sleeptimer.daemon = True
        t_sleeptimer.start()

    while True:
        time.sleep(10)


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
            file_full_path = os.path.join(folderscreen,file)
            if os.path.isfile(file_full_path) and file.endswith(".png"):
                #Delete files older than x days
                if os.stat(file_full_path).st_mtime < now - int(minutes) * 60:
                    os.remove(file_full_path)
                    log.debug('deleteOldScreens: File Removed : ' + file_full_path)

        if args.save_success:

            if not os.path.exists(args.successsave_path):
                log.info('deleteOldScreens: Save directory created')
                os.makedirs(args.successsave_path)

            log.debug('deleteOldScreens: Cleanup Folder: ' + str(foldersuccess))
            for file in os.listdir(foldersuccess):
                file_full_path = os.path.join(foldersuccess,file)
                if os.path.isfile(file_full_path) and file.endswith(".jpg"):
                    #Delete files older than x days
                    if os.stat(file_full_path).st_mtime < now - int(minutes) * 60:
                        os.remove(file_full_path)
                        log.debug('deleteOldScreens: File Removed : ' + file_full_path)

        log.info('deleteOldScreens: Search/Delete Screenshots finished')
        time.sleep(3600)


def sleeptimer(sleeptime):
    global sleep
    global telnMore
    tmFrom = datetime.datetime.strptime(sleeptime[0],"%H:%M")
    log.debug("sleeptimer: tmFrom: %s" % str(tmFrom))
    tmTil = datetime.datetime.strptime(sleeptime[1],"%H:%M") + datetime.timedelta(hours = 24)
    log.debug("sleeptimer: tmTil: %s" % str(tmTil))
    while True:
        # we assume sleep is always at night...
        tmNow = datetime.datetime.strptime(datetime.datetime.now().strftime('%H:%M'),"%H:%M")
        tmNowNextDay = tmNow + datetime.timedelta(hours = 24)
        # log.debug("tmNow: %s" % str(tmNow))

        if tmNow >= tmFrom and tmNowNextDay < tmTil:
            log.info('sleeptimer: Going to sleep - byebye')
            # Stopping pogo...
            if telnMore:
                telnMore.stopApp("com.nianticlabs.pokemongo")
                telnMore.clearAppCache("com.nianticlabs.pokemongo")
            sleep = True

            while sleep:
                tmNow = datetime.datetime.strptime(datetime.datetime.now().strftime('%H:%M'),"%H:%M")
                tmNowNextDay = tmNow + datetime.timedelta(hours = 24)
                log.debug('sleeptimer: Still sleeping, current time... %s' % str(tmNow))
                if tmNow < tmFrom and tmNowNextDay >= tmTil:
                    log.warning('sleeptimer: Wakeup - here we go ...')
                    # Turning screen on and starting app
                    if telnMore:
                        telnMore.turnScreenOn()
                        telnMore.startApp("sleeptimer: com.nianticlabs.pokemongo")
                    sleep = False
                    break
                time.sleep(1)
        time.sleep(1)


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
    curTime = time.time()
    successfulStop = stopPogo()
    # TODO: errorhandling if it returned false, maybe try again next round?
    # TODO: check if pogo was closed...
    log.debug("restartPogo: stop pogo resulted in %s" % str(successfulStop))
    if successfulStop:
        return startPogo(False)
        # TODO: handle login screen... ?
    else:
        return False


def tabOutAndInPogo():
    global telnMore
    telnMore.startApp("de.grennith.rgc.remotegpscontroller")
    time.sleep(3)
    telnMore.startApp("com.nianticlabs.pokemongo")
    time.sleep(2)


def stopPogo():
    global telnMore
    stopResult = telnMore.stopApp("com.nianticlabs.pokemongo")
    return stopResult is not None and "OK" in stopResult


def startPogo(withLock=True):
    global telnMore
    global lastPogoRestart
    global windowLock
    if withLock:
        windowLock.acquire()
    curTime = time.time()
    telnMore.clearAppCache("com.nianticlabs.pokemongo")
    time.sleep(1)
    startResult = telnMore.startApp("com.nianticlabs.pokemongo")
    reachedRaidtab = False
    if startResult is not None and "OK" in startResult:
        log.warning("Starting pogo...")
        #time.sleep(args.post_pogo_start_delay)
        lastPogoRestart = curTime

        # let's handle the login and stuff
        reachedRaidtab = getToRaidscreen(15, True)

    if withLock:
        windowLock.release()
    return reachedRaidtab


def getToRaidscreen(maxAttempts, checkAll=False):
    # check for any popups (including post login OK)
    global windowLock
    global lastScreenshotTaken

    log.debug("getToRaidscreen: Trying to get to the raidscreen with %s max attempts..." % str(maxAttempts))

    log.info("getToRaidscreen: Attempting to retrieve screenshot before checking windows")
    if not screenWrapper.getScreenshot('screenshot.png'):
        log.error("getToRaidscreen: Failed retrieving screenshot before checking for closebutton")
        return False
    else:
        lastScreenshotTaken = time.time()
    attempts = 0
    while not pogoWindowManager.checkRaidscreen('screenshot.png', 123):
        if attempts > maxAttempts:
            # could not reach raidtab in given maxAttempts
            log.error("getToRaidscreen: Could not get to raidtab within %s attempts" % str(maxAttempts))
            return False
        # not using continue since we need to get a screen before the next round...
        found = pogoWindowManager.checkSpeedwarning('screenshot.png', 123)
        if checkAll:
            # also check for login and stuff...
            if not found and pogoWindowManager.checkPostLoginOkButton('screenshot.png', 123):
                log.info("getToRaidscreen: Found post-login OK button")
                found = True
                time.sleep(0.5)
            if not found and pogoWindowManager.checkPostLoginNewsMessage('screenshot.png', 123):
                log.info("getToRaidscreen: Found post login news message")
                found = True
                time.sleep(0.5)
        if not found and pogoWindowManager.checkCloseExceptNearbyButton('screenshot.png', 123):
            log.info("getToRaidscreen: Found (X) button (except nearby)")
            found = True
            time.sleep(0.5)
        if not found and pogoWindowManager.checkWeatherWarning('screenshot.png', 123):
            log.info("getToRaidscreen: Found weather warning")
            found = True
            time.sleep(0.5)
        if not found and pogoWindowManager.checkGameQuitPopup('screenshot.png', 123):
            log.info("getToRaidscreen: Found game quit popup")
            found = True
            time.sleep(0.5)

        log.info("getToRaidscreen: Previous checks found popups: %s" % str(found))
        if not found:
            log.info("getToRaidscreen: Previous checks found nothing. Checking nearby open")
            pogoWindowManager.checkNearby('screenshot.png', 123)

        log.info("getToRaidscreen: Attempting to retrieve screenshot checking windows")
        if screenWrapper.getScreenshot('screenshot.png'):
            lastScreenshotTaken = time.time()
        else:
            log.error("getToRaidscreen: Failed getting screenshot while checking windows")
            return False

        time.sleep(args.post_screenshot_delay)
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
    if not telnMore.isPogoTopmost():
        log.warning("Starting Pogo")
        startPogo()


def reopenRaidTab():
    global pogoWindowManager
    log.info("reopenRaidTab: Attempting to retrieve screenshot before checking raidtab")
    if not screenWrapper.getScreenshot('screenshot.png'):
        log.error("reopenRaidTab: Failed retrieving screenshot before checking for closebutton")
        return
    if pogoWindowManager.isOtherCloseButtonPresent('screenshot.png', 123):
        screenWrapper.backButton()
        log.debug("reopenRaidTab: Closebutton was present, checking raidscreen...")
        telnMore.clearAppCache("com.nianticlabs.pokemongo")
        time.sleep(1)
        # screenWrapper.getScreenshot('screenshot.png')
        # pogoWindowManager.checkRaidscreen('screenshot.png', 123)
        getToRaidscreen(3)
        time.sleep(1)


# supposed to be running mostly in the post walk/teleport delays...
def checkSpeedWeatherWarningThread():
    global sleep
    global runWarningThreadEvent
    global windowLock
    global telnMore
    while True:
        while sleep or not runWarningThreadEvent.isSet():
            time.sleep(0.5)
        log.debug("checkSpeedWeatherWarningThread: acquiring lock")
        windowLock.acquire()

        log.debug("checkSpeedWeatherWarningThread: Checking if pogo is running...")
        if not telnMore.isPogoTopmost():
            log.warning("checkSpeedWeatherWarningThread: Starting Pogo")
            startPogo(False)
            windowLock.release()
            return
        reachedRaidscreen = getToRaidscreen(4, True)
        if reachedRaidscreen:
            log.debug("checkSpeedWeatherWarningThread: checkSpeedWeatherWarningThread: reached raidscreen...")
        else:
            log.debug("checkSpeedWeatherWarningThread: did not reach raidscreen in 4 attempts")
        log.debug("checkSpeedWeatherWarningThread: releasing lock")
        windowLock.release()
        time.sleep(args.post_teleport_delay)


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

    log.info("main: Starting TelnetGeo Client")
    telnGeo = TelnetGeo(str(args.tel_ip), args.tel_port, str(args.tel_password))

    log.info("main: Starting dbWrapper")
    dbWrapper = DbWrapper(str(args.dbip), args.dbport, args.dbusername, args.dbpassword, args.dbname, args.timezone)
    updateRaidQueue(dbWrapper)
    lastRaidQueueUpdate = time.time()

    if lastPogoRestart is None:
        lastPogoRestart = time.time()

    route = getJsonRoute(args.file, args.gym_distance, args.max_count_gym_sum_up_around_gym)

    log.info("main: Route to be taken: %s, amount of coords: %s" % (str(route), str(len(route))))
    log.info("main: Max_distance before teleporting: %s" % args.max_distance)
    log.info("main: Checking if screen is on and pogo is running")

    if not sleep:
        turnScreenOnAndStartPogo()

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

            # Restart pogo every now and then...
            if args.restart_pogo > 0:
                #log.debug("main: Current time - lastPogoRestart: %s" % str(curTime - lastPogoRestart))
                # if curTime - lastPogoRestart >= (args.restart_pogo * 60):
                locationCount += 1
                if locationCount > args.restart_pogo:
                    log.error("scanned " + str(args.restart_pogo) + " locations, restarting pogo")
                    restartPogo()
                    locationCount = 0

            # let's check for speed and weather warnings while we're walking/teleporting...
            runWarningThreadEvent.set()
            lastLat = curLat
            lastLng = curLng
            egghatchLocation = False
            log.debug("main: Checking for raidqueue priority. Current time: %s, Current queue: %s" % (str(time.time()), str(nextRaidQueue)))
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

            log.debug("main: next stop: %s, %s" % (str(curLat), str(curLng)))
            log.debug('main: LastLat: %s, LastLng: %s, CurLat: %s, CurLng: %s' % (lastLat, lastLng, curLat, curLng))
            # get the distance from our current position (last) to the next gym (cur)
            distance = getDistanceOfTwoPointsInMeters(float(lastLat), float(lastLng), float(curLat), float(curLng))
            log.info('main: Moving %s meters to the next position' % distance)
            delayUsed = 0
            if (args.speed == 0 or
                (args.max_distance and args.max_distance > 0 and distance > args.max_distance)
                    or (lastLat == 0.0 and lastLng == 0.0)):
                log.info("main: Teleporting...")
                telnGeo.setLocation(curLat, curLng, 0)
                delayUsed = args.post_teleport_delay
            else:
                log.info("main: Walking...")
                telnGeo.walkFromTo(lastLat, lastLng, curLat, curLng, args.speed)
                delayUsed = args.post_walk_delay
            time.sleep(delayUsed)

            # ok, we should be at the next gym, check for errors and stuff
            # TODO: improve errorhandling by checking results and trying again and again
            # not using continue to always take a new screenshot...
            log.debug("main: Clearing event, acquiring lock")
            runWarningThreadEvent.clear()
            windowLock.acquire()
            log.debug("main: Lock acquired")
            log.debug("main: Checking if pogo is running...")
            if not telnMore.isPogoTopmost():
                log.warning("main: Starting Pogo")
                startPogo(False)
                windowLock.release()
                continue

            log.info("main: Attempting to retrieve screenshot before checking windows")
            # check if last screenshot is way too old to be of use...
            # log.fatal(lastScreenshotTaken)
            compareToTime = time.time() - lastScreenshotTaken
            if not lastScreenshotTaken or compareToTime > 1:
                log.info("main: last screenshot too old, getting a new one")
                # log.error("compareToTime: %s" % str(compareToTime))
                # log.error("delayUsed: %s" % str(delayUsed))
                if not screenWrapper.getScreenshot('screenshot.png'):
                    log.error("main: Failed retrieving screenshot before checking windows")
                    windowLock.release()
                    break
                    # failcount += 1
                    # TODO: consider proper errorhandling?
                    # even restart entire thing? VNC dead means we won't be using the device
                    # maybe send email? :D
                else:
                    lastScreenshotTaken = time.time()
            while not getToRaidscreen(12):
                if failcount > 5:
                    log.fatal("main: failed to find raidscreen way too often. Exiting")
                    sys.exit(1)
                failcount += 1
                log.error("main: Failed to find the raidscreen multiple times in a row. Stopping pogo and taking a "
                          "break of 5 minutes")
                stopPogo()
                time.sleep(300)
                startPogo(False)
            failcount = 0

            # well... we are on the raidtab, but we want to reopen it every now and then, so screw it
            reopenedRaidTab = False
            # if not egghatchLocation and math.fmod(i, 30) == 0:
            #    log.warning("main: Closing and opening raidtab every 30 locations scanned... Doing so")
            #    reopenRaidTab()
            #    tabOutAndInPogo()
            #    screenWrapper.getScreenshot('screenshot.png')
            #    reopenedRaidTab = True

            if args.last_scanned:
                log.info('main: Set new scannedlocation in Database')
                dbWrapper.setScannedLocation(str(curLat), str(curLng), str(curTime))

            log.info("main: Checking raidcount and copying raidscreen if raids present")
            countOfRaids = pogoWindowManager.readRaidCircles('screenshot.png', 123)
            if countOfRaids == -1 and not reopenedRaidTab:
                # reopen raidtab and take screenshot...
                log.warning("main: Count present but no raid shown, reopening raidTab")
                reopenRaidTab()
                tabOutAndInPogo()
                screenWrapper.getScreenshot('screenshot.png')
                countOfRaids = pogoWindowManager.readRaidCircles('screenshot.png', 123)
        #    elif countOfRaids == 0:
        #        emptycount += 1
        #        if emptycount > 30:
        #            emptycount = 0
        #            log.error("Had 30 empty scans, restarting pogo")
        #            restartPogo()
            log.debug("main: countOfRaids: %s" % str(countOfRaids))
            if countOfRaids > 0:
                curTime = time.time()
                copyfile('screenshot.png', args.raidscreen_path
                    + '/raidscreen_' + str(curTime) + "_" + str(curLat) + "_"
                    + str(curLng) + "_" + str(countOfRaids) + '.png')
            log.debug("main: Releasing lock")
            windowLock.release()


def observer(scrPath, width, height):
        observer = Observer()
        observer.schedule(checkScreenshot(width, height), path=scrPath)
        observer.start()


if __name__ == '__main__':
    main()
