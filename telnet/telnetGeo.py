from telnetClient import *
import gpxdata
import datetime
import time
import logging
log = logging.getLogger()


class TelnetGeo:
    UPDATE_INTERVAL = 0.4
    def __init__(self, ip, port, password):
        #Throws ValueError if unable to connect!
        #catch in code using this class
        self.telnetClient = TelnetClient(ip, port, password)

    def setLocation(self, lat, lng, alt):
        return self.telnetClient.sendCommand("geo fix %s %s %s\r\n" % (lat, lng, alt), 15)

    #coords need to be float values
    #speed integer with km/h
    #######
    ### This blocks!
    #######
    def walkFromTo(self, startLat, startLng, destLat, destLng, speed):
        startLat = float(startLat)
        startLng = float(startLng)
        destLat = float(destLat)
        destLng = float(destLng)
        start = gpxdata.TrackPoint(startLat, startLng, 1.0, datetime.datetime(2010, 1, 1, 0, 0, 0))
        dest = gpxdata.TrackPoint(destLat, destLng, 1.0, datetime.datetime(2010, 1, 1, 0, 0, 15))

        t_speed = None
        if speed:
            t_speed = speed / 3.6
        log.debug("walkFromTo: calling __walkTrackSpeed")
        self.__walkTrackSpeed(start, t_speed, dest)

    #TODO: errorhandling, return value
    def __walkTrackSpeed(self, start, speed, dest):
        log.debug("__walkTrackSpeed: called, calculating distance and travel_time")
        distance = start.distance(dest)
        travel_time = distance / speed

        if travel_time <= TelnetGeo.UPDATE_INTERVAL:
            log.debug("__walkTrackSpeed: travel_time is <= UPDATE_INTERVAL")
            time.sleep(travel_time)

        log.debug("__walkTrackSpeed: starting to walk")
        while travel_time > TelnetGeo.UPDATE_INTERVAL:
            log.debug("__walkTrackSpeed: sleeping for %s" % str(TelnetGeo.UPDATE_INTERVAL))
            time.sleep(TelnetGeo.UPDATE_INTERVAL)
            log.debug("__walkTrackSpeed: Next round")
            travel_time -= TelnetGeo.UPDATE_INTERVAL
            # move GEOFIX_UPDATE_INTERVAL*speed meters
            # in straight line between last_point and point
            course = start.course(dest)
            distance = TelnetGeo.UPDATE_INTERVAL * speed
            start = start + gpxdata.CourseDistance(course, distance)
            startLat = start.lat
            startLng = start.lon
            log.debug("__walkTrackSpeed: sending location")
            self.setLocation(repr(startLat), repr(startLng), "")
            log.debug("__walkTrackSpeed: done sending location")
        #print("Done")
