###
#
# Telnet commands that can be executed to set the Location
# Either walk or teleport
#
###

import socket

class TelnetGeo:
    UPDATE_INTERVAL = 0.3
    def __init__(self, ip, port, password):
        self.ip = ip
        self.port = port
        self.password = password

        self.__s = socket.socket()
        self.alive = False
        self.authenticated = True
        try:
            self.__s.connect((self.ip, self.port))
            self.alive = True
        except socket.error as ex:
            print("Error connecting to %s:%s (%s)" % (ip, port, ex))
            #thread.interrupt_main()
        print(self.authenticate(password))

    def __del__(self):
        self.__s.close()

    def __sendCommand(self, command):
        if (not self.alive or not self.authenticated):
            raise ValueError('Socket not alive or not authenticated')

        self.__s.send(command)
        x = self.__s.recv(1024)
        if "OK" in x:
            return True
        else:
            return False

    def authenticate(self, password):
        return self.__sendCommand("auth %s\r\n" % (password))

    def setLocation(self, lat, lng, alt):
        return self.__sendCommand("geo fix %s %s %s\r\n" % (lat, lng, alt))

    #coords need to be float values
    #speed integer with km/h
    def walkFromTo(self, startLat, startLng, destLat, destLng, speed):
        startLat = float(startLat)
        startLng = float(startLng)
        destLat = float(destLat)
        destLng = float(destLng)
        start = gpxdata.TrackPoint(start_lat, start_lon, 1.0, datetime.datetime(2010, 1, 1, 0, 0, 0))
        dest = gpxdata.TrackPoint(dest_lat, dest_lon, 1.0, datetime.datetime(2010, 1, 1, 0, 0, 15))

        t_speed = None
        if speed:
            t_speed = speed / 3.6
        self.__walkTrackSpeed(start, t_speed, dest)

    def __walkTrackSpeed(self, start, speed, dest):
        distance = start.distance(dest)
        travel_time = distance / speed

        if travel_time <= UPDATE_INTERVAL:
            time.sleep(travel_time)

        while travel_time > UPDATE_INTERVAL:
            time.sleep(UPDATE_INTERVAL)
            travel_time -= UPDATE_INTERVAL
            # move GEOFIX_UPDATE_INTERVAL*speed meters
            # in straight line between last_point and point
            course = start.course(dest)
            distance = UPDATE_INTERVAL * speed
            start = start + gpxdata.CourseDistance(course, distance)
            startLat = start.lat
            startLng = start.lon
            self.setLocation(repr(startLat), repr(startLng), "")
        print("Done")
