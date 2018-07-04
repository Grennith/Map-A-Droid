import time
from threading import Thread, Event
import logging
from colorlog import ColoredFormatter
from walkerArgs import parseArgs
import sys
import os
import math
#from vnc import vncWrapper
#from detect_text import check_login, check_message, check_Xbutton, check_speedmessage, check_quitbutton, check_raidscreen
#from copyMons import copyMons
#from  scanner import start_detect

#internal imports

#import sys
#sys.path.insert(0, 'vnc')
#sys.path.insert(0, 'routecalc')

from routecalc.calculate_route import getJsonRoute
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

    #thread.start_new_thread(main_thread, ('test'))

    t = Thread(target=main_thread,
                       name='main')
    t.daemon = True
    t.start()
    log.info('Starting Thread....')
    while True:
        pass
    #loop = asyncio.get_event_loop()
    #tasks = [
    #    asyncio.async(getVNCPic()),
    #    asyncio.async(check_login()),
    #    asyncio.async(check_message()),
    #    asyncio.async(check_Xbutton())]

    #loop.run_until_complete(asyncio.wait(tasks))
    #loop.run_forever()
    #loop.close()

    # Hier muss noch der Async Job starter rein. Aktuell nur einzelne Jobs zum testen


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

def getDistanceOfTwoPointsInMeters(startLat, startLng, destLat, destLng):
    # approximate radius of earth in km
    R = 6373.0

    lat1 = math.radians(startLat)
    lon1 = math.radians(startLng)
    lat2 = math.radians(destLat)
    lon2 = math.radians(destLng)

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = R * c

    distanceInMeters = distance * 1000
    return distanceInMeters



def main_thread():
    vncWrapper = VncWrapper(str(args.vnc_ip,), 1, args.vnc_port, args.vnc_password)
    telnGeo = TelnetGeo(str(args.tel_ip), args.tel_port, str(args.tel_password))
    telnMore = TelnetMore(str(args.tel_ip), args.tel_port, str(args.tel_password))
    pogoWindowManager = PogoWindows(str(args.vnc_ip,), 1, args.vnc_port, args.vnc_password)

    route = getJsonRoute(args.file)
    lastPogoRestart = time.time()
    print(route)
    #sys.exit(0)
    log.info(args.max_distance)

    while True:
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
            else:
                log.info("Walking")
                log.info(args.speed)
                telnGeo.walkFromTo(lastLat, lastLng, curLat, curLng, args.speed)

            #ok, we should be at the next gym, check for errors and stuff
            #TODO: improve errorhandling by checking results and trying again and again
            vncWrapper.getScreenshot('screenshot.png')
            pogoWindowManager.checkLogin('screenshot.png', 123)
            pogoWindowManager.checkMessage('screenshot.png', 123)
            pogoWindowManager.checkClosebutton('screenshot.png', 123)
            pogoWindowManager.checkSpeedmessage('screenshot.png', 123)
            #pogoWindowManager.checkQuitbutton('screenshot.png', 123)
            pogoWindowManager.checkRaidscreen('screenshot.png', 123)


            #we should now see the raidscreen, let's take a screenshot of it
            log.info("Saving raid screenshot")
            vncWrapper.getScreenshot('screenshots/nextRaidscreen' + str(time.time()) + '.jpg')

            #we got the latest raids. To avoid the mobile from killing apps,
            #let's restart pogo every 90minutes or whatever TODO: consider args
            curTime = time.time()
            if (curTime - lastPogoRestart >= (90 * 60)):
                #time for a restart
                successfulRestart = telnMore.restartApp("com.nianticlabs.pokemongo")
                #TODO: errorhandling if it returned false, maybe try again next round?
                if successfulRestart:
                    lastPogoRestart = curTime
                time.sleep(25) #just sleep for a couple seconds to have the game come back up again
                #TODO: handle login screen...

        #vncWrapper.getScreenshot('checkErrors.jpg')

        #check_login()
        #check_quitbutton()
        #check_message()
        #check_Xbutton()
        #check_speedmessage()
        #check_raidscreen()
        #start_detect()
        #time.sleep(10)


if __name__ == '__main__':
    main()
