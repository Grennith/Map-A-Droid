#!/usr/bin/env python

# GPX from google maps route: http://www.gpsvisualizer.com/convert_input
# Or export directly from http://map.project-osrm.org

### stdlib packages
import os
import socket
import argparse
import sys
import select
import time
import threading
import thread
import datetime


### external deps
try:
    import dateutil.parser
    assert dateutil.parser  # pyflakes
except ImportError:
    print("package \"python-dateutil\" is required. exiting")
    sys.exit(2)
### bundled packages
import gpxdata
###

UPDATE_INTERVAL = 0.3

start_lat = 49.000
start_lon = 9.0000
dest_lat = 49.000
dest_lon = 9.000

def main(args):
    global start_lat
    global start_lon
    startArg = args.start.split(',')
    destArg = args.destination.split(',')

    start_lat = float(startArg[0])
    start_lon = float(startArg[1])
    dest_lat = float(destArg[0])
    dest_lon = float(destArg[1])


    #start_lat = 49.01242164
    #start_lon = 8.403430581
    #dest_lat = 49.01241460
    #dest_lon = 8.404868245
    start = gpxdata.TrackPoint(start_lat, start_lon, 1.0, datetime.datetime(2010, 1, 1, 0, 0, 0))
    dest = gpxdata.TrackPoint(dest_lat, dest_lon, 1.0, datetime.datetime(2010, 1, 1, 0, 0, 15))

    point = gpxdata.Point(start_lat, start_lon, 1.0, datetime.datetime(2010, 1, 1, 0, 0, 0))
    #start the geofix sending...
    geofix_thread = threading.Thread(target=start_geofix, args=(args,))
    geofix_thread.daemon = True
    geofix_thread.start()

    t_speed = None
    if args.speed:
        t_speed = args.speed / 3.6

    print("Location mocking started.")
    walk_track_speed(dest, t_speed, point)

def walk_track_speed(dest, speed, point):
    global start_lat
    global start_lon

    distance = point.distance(dest)
    travel_time = distance / speed  # in seconds

    if travel_time <= UPDATE_INTERVAL:
        time.sleep(travel_time)
    while travel_time > UPDATE_INTERVAL:
        time.sleep(UPDATE_INTERVAL)
        travel_time -= UPDATE_INTERVAL
        # move GEOFIX_UPDATE_INTERVAL*speed meters
        # in straight line between last_point and point
        course = point.course(dest)
        distance = UPDATE_INTERVAL * speed
        point = point + gpxdata.CourseDistance(course, distance)
        start_lat = point.lat
        start_lon = point.lon

    start_lat = point.lat
    start_lon = point.lon
    print("Done")
    sys.exit(0)

def start_geofix(args):
    s = socket.socket()
    try:
        s.connect((args.ip, args.port))
    except socket.error as ex:
        print("Error connecting to %s:%s (%s)" % (args.ip, args.port, ex))
        thread.interrupt_main()

    print("Start_geofix")
    try:
        while True:
            rlist, wlist, _ = select.select([s], [s], [])
            #print(curr_lat)
            if s in rlist:
                x = s.recv(1024)
                if "KO: password required. Use 'password' or 'auth'" in x:
                    #s.close()
                    if (args.password and len(args.password) > 0):
                        s.send("auth %s\r\n" % (args.password))
                    else:
                        print("Password protection is enabled but no password was set.")
                        s.close()
                        thread.interrupt_main()
                        sys.exit(1)
                if x == '':
                    s.close()
                    print("Connection closed.")
                    thread.interrupt_main()
            if s in wlist:
                s.send("geo fix %f %f\r\n" % (start_lat, start_lon))
                #print("Sending geo fix")
            time.sleep(UPDATE_INTERVAL)
    except socket.error as ex:
        print(ex)
        thread.interrupt_main()

if __name__ == '__main__':
    args_parser = argparse.ArgumentParser()
    args_parser.add_argument("-i", "--ip", help="connect to MockGeoFix using this IP address",
                             required=True)
    args_parser.add_argument("-p", "--port", default=5554, help="default: 5554", type=int)
    args_parser.add_argument("-d", "--destination", required=True)
    args_parser.add_argument("-c", "--start", required=True)
    args_parser.add_argument("-s", "--speed", help="speed in km/h (takes precedence over -S)",
                             required=True, type=float)
    args_parser.add_argument("-P", "--password", help="Password to auth with",
                            required=False)
    args = args_parser.parse_args()

    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    try:
        main(args)
    except KeyboardInterrupt:
        print("Exiting.")
