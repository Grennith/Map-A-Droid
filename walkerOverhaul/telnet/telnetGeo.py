from telnetClient import *
import gpxdata
import datetime
import time

class TelnetGeo:
    UPDATE_INTERVAL = 0.4
    def __init__(self, ip, port, password):
        #Throws ValueError if unable to connect!
        #catch in code using this class
        self.telnetClient = TelnetClient(ip, port, password)

    def setLocation(self, lat, lng, alt):
        return self.telnetClient.sendCommand("geo fix %s %s %s\r\n" % (lat, lng, alt))

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
        self.__walkTrackSpeed(start, t_speed, dest)

    #TODO: errorhandling, return value
    def __walkTrackSpeed(self, start, speed, dest):
        distance = start.distance(dest)
        travel_time = distance / speed

        if travel_time <= TelnetGeo.UPDATE_INTERVAL:
            time.sleep(travel_time)

        while travel_time > TelnetGeo.UPDATE_INTERVAL:
            time.sleep(TelnetGeo.UPDATE_INTERVAL)
            travel_time -= TelnetGeo.UPDATE_INTERVAL
            # move GEOFIX_UPDATE_INTERVAL*speed meters
            # in straight line between last_point and point
            course = start.course(dest)
            distance = TelnetGeo.UPDATE_INTERVAL * speed
            start = start + gpxdata.CourseDistance(course, distance)
            startLat = start.lat
            startLng = start.lon
            self.setLocation(repr(startLat), repr(startLng), "")
        #print("Done")
