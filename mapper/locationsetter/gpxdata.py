# ----------------------------------------
# Copyright (C) 2008-2011  Frank Paehlke
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
# ----------------------------------------

import codecs
import math
import sys
import time
from os.path import basename
from xml.dom.minidom import parse, getDOMImplementation
import dateutil.parser
import datetime
import warnings

# Python 3.x compatibility
if sys.version_info[0] >= 3:
    basestring = str
    unicode = str

__all__ = [ 'Util', 'LatLon', 'CourseDistance', 'Point', 'TrackPoint', 'RoutePoint', 'Waypoint',
            'Track', 'TrackSegment', 'Route' ]

# ----------------------------------------

class Util:
    """
    Several static utility functions for geodesic calculations and map projections.

    These functions do not aim at maximum accuracy - the Geoid is modeled
    as a perfect sphere with radius 6371 km.

    Most formulas were taken from:
    Aviation Formulary by Ed Williams,
    http://williams.best.vwh.net/avform.htm
    """

    r_earth = 6.371e6 # earth radius [m]

    @staticmethod
    def haversin (x):
        """
        haversin(x) = sin^2 (x/2)
        """
        sinx2 = math.sin(x/2.0)
        return sinx2*sinx2

    @staticmethod
    def inv_haversin (x):
        """
        inverse of haversin(x)
        """
        return 2.0 * math.asin(math.sqrt(x))

    @classmethod
    def toCartesian (cls, lat, lon):
        """
        convert latitude/longitude [degrees] to cartesian coordinates (x, y, z) [m]
        """
        lat_rad = math.radians(lat)
        lon_rad = math.radians(lon)
        cos_lat = math.cos(lat_rad)
        return ( cls.r_earth * cos_lat * math.cos(lon_rad),
                 cls.r_earth * cos_lat * math.sin(lon_rad),
                 cls.r_earth * math.sin(lat_rad) )

    @staticmethod
    def fromCartesian (x, y, z):
        """
        convert cartesian coordinates [m] to latitude/longitude [degrees]
        """
        lat_rad = math.atan2(z, math.hypot(x,y))
        lon_rad = math.atan2(y, x)
        return (math.degrees(lat_rad), math.degrees(lon_rad))

    @classmethod
    def course (cls, lat1, lon1, lat2, lon2):
        """
        initial course [degrees] to reach (lat2, lon2) from (lat1, lon1) on a great circle

        range of returned values:
        -180 < course <= 180
        (-90 = west, 0 = north, 90 = east, 180 = south)
        """
        if lat1 + 1e-10 > 90.0:
            return 180.0 # starting from north pole -> the only direction is south
        elif lat1 - 1e-10 < -90.0:
            return 0.0   # starting from south pole -> the only direction is north
        lat1rad = math.radians(lat1)
        lat2rad = math.radians(lat2)
        londiff = math.radians(lon2 - lon1)
        course_rad = math.atan2(
            math.sin(londiff) * math.cos(lat2rad),
            math.cos(lat1rad) * math.sin(lat2rad) - math.sin(lat1rad) * math.cos(lat2rad) * math.cos(londiff))
        return math.degrees(course_rad)

    @classmethod
    def distance (cls, lat1, lon1, lat2, lon2):
        """
        distance [m] between two geographical coordinates

        Note: this method has been renamed from geo_distance() to distance().
        The old method Util.distance(p1, p2) was removed - use LatLon.distance() instead.
        """
        lat1rad = math.radians(lat1)
        lat2rad = math.radians(lat2)
        londiff = math.radians(lon2-lon1)
        return cls.r_earth * cls.inv_haversin (
            cls.haversin(lat2rad - lat1rad) +
            math.cos(lat1rad) * math.cos(lat2rad) * cls.haversin(londiff))

    @classmethod
    def geo_distance (cls, lat1, lon1, lat2, lon2):
        """
        deprecated - replaced by distance()
        """
        warnings.warn("geo_distance() is deprecated - use distance() instead", DeprecationWarning)
        return distance(cls, lat1, lon1, lat2, lon2)

    @classmethod
    def courseAndDistance (cls, lat1, lon1, lat2, lon2):
        """
        returns pair (initial course [degrees], distance [m]) to reach (lat2,lon2) from (lat1,lon1) on a great circle
        """
        lat1rad = math.radians(lat1)
        lat2rad = math.radians(lat2)
        londiff = math.radians(lon2 - lon1)
        sin_lat1 = math.sin(lat1rad)
        sin_lat2 = math.sin(lat2rad)
        cos_lat1 = math.cos(lat1rad)
        cos_lat2 = math.cos(lat2rad)
        distance_rad = cls.inv_haversin (
            cls.haversin(lat2rad - lat1rad) +
            cos_lat1 * cos_lat2 * cls.haversin(londiff))
        course_rad = math.atan2(
            math.sin(londiff) * cos_lat2,
            cos_lat1 * sin_lat2 - sin_lat1 * cos_lat2 * math.cos(londiff))
        return (math.degrees(course_rad), cls.r_earth * distance_rad)

    @classmethod
    def endPosition (cls, lat1, lon1, course, distance):
        """
        calculate end position when traveling a certain distance on a great circle

        Parameters: initial latitude/longitude [degrees], initial course [degrees], distance [m]
        Returns: pair (lat, lon) with latitude/longitude [degrees] of end point
        """
        if lat1 + 1e-10 > 90:
            raise ValueError("There are no defined directions when starting from the north pole")
        elif lat1 - 1e-10 < -90:
            raise ValueError("There are no defined directions when starting from the south pole")
        lat1rad = math.radians(lat1)
        lon1rad = math.radians(lon1)
        d_rad = distance / cls.r_earth
        c_rad = math.radians(course)
        sin_lat1 = math.sin(lat1rad)
        cos_lat1 = math.cos(lat1rad)
        sin_d = math.sin(d_rad)
        cos_d = math.cos(d_rad)
        sin_lat = sin_lat1 * cos_d + cos_lat1 * sin_d * math.cos(c_rad)
        londiff = math.atan2(
            math.sin(c_rad) * sin_d * cos_lat1,
            cos_d - sin_lat1 * sin_lat)
        lat = math.degrees(math.asin(sin_lat))
        lon = (lon1 + math.degrees(londiff)) % 360
        if lon > 180:
            lon -= 360
        return (lat, lon)

    @classmethod
    def interpolate (cls, lat1, lon1, lat2, lon2, ratio):
        """
        interpolation of intermediate points on the great circle through (lat1, lon1) and (lat2, lon2)

        For ratio=0, the method returns (lat1, lon1)
        For ratio=1, the method returns (lat2, lon2)
        """
        d_rad = cls.distance (lat1, lon1, lat2, lon2) / cls.r_earth
        sin_d = math.sin(d_rad)
        A = math.sin((1-ratio)*d_rad) / sin_d
        B = math.sin(ratio*d_rad) / sin_d
        x1, y1, z1 = cls.toCartesian(lat1, lon1)
        x2, y2, z2 = cls.toCartesian(lat2, lon2)
        x, y, z = A*x1+B*x2, A*y1+B*y2, A*z1+B*z2
        return cls.fromCartesian(x, y, z)

    @classmethod
    def transMercator (cls, lat, lon, centerlon=0.0):
        """
        Transversal Mercator projection - returns (x,y) tuple (unit:  m)

        centerlon = longitude [degrees] of central meridian (x=0)
        """
        lat_rad = math.radians(lat)
        lon_rad = math.radians(lon-centerlon)
        x = cls.r_earth * math.atanh(math.sin(lon_rad) * math.cos(lat_rad))
        y = cls.r_earth * math.atan(math.tan(lat_rad) / math.cos(lon_rad))
        return x,y

    if sys.version_info[0] >= 3:
        @staticmethod
        def writexml (document, file, encoding):
            """
            Write an xml.dom "Document" to a file - Python 3 version
            """
            document.writexml(file, addindent=' ',newl='\n', encoding=encoding)
    else:
        @staticmethod
        def writexml (document, file, encoding):
            """
            Write an xml.dom DOM "Document" to a file - Python 2 version
            """
            document.writexml(codecs.getwriter (encoding)(file), addindent=' ',newl='\n', encoding=encoding)

# ----------------------------------------

class LatLon:
    """
    Representation of a geographic coordinate.

    Properties:
    lat  latitude [degrees]   (-90 <= lat <= 90)
    lon  longitude [degrees]  (-180 < lon <= 180)

    Constructor:
    LatLon(lat, lon)
    """

    @property
    def lat(self):
        """
        latitude [degrees]

        range: -90 <= lat <= 90
        """
        return self._lat

    @property
    def lon(self):
        """
        longitude [degrees]

        range: -180 < lon <= 180
        """
        return self._lon

    def __init__ (self, lat, lon):
        if lat < -90 or lat > 90:
            raise ValueError ("lat must be between -90 and 90")
        self._lat = float(lat)
        # normalize longitude to the interval ]-180,180]
        self._lon = float(lon % 360)
        if self._lon > 180:
            self._lon -= 360

    def __repr__ (self):
        return "".join(["LatLon(", repr(self._lat), ",", repr(self._lon), ")"])

    def __str__ (self):
        return "".join(["LatLon(", str(self._lat), ",", str(self._lon), ")"])

    def distance (self, p, q=None):
        """
        calculate geographic distance [m]

        distance(p):
            distance between self and p

        distance(p,q):
            distance between self and the great circle that connects p and q
            positive: self is on the right when going from p to q
            negative: self is on the left when going from p to q
        """
        if q is None:
            if not isinstance(p, LatLon):
                raise TypeError("argument must be of class LatLon")
            return Util.distance(self._lat, self._lon, p.lat, p.lon)
        else:
            if not isinstance(p, LatLon) or not isinstance (q, LatLon):
                raise TypeError("arguments must be of class LatLon")
            # calculate courses from p to q and from p to self
            course_p_q = Util.course(p._lat, p._lon, q._lat, q._lon)
            course_p_self, dist_p_self = Util.courseAndDistance(p._lat, p._lon, self._lat, self._lon)
            # calculate distance to great circle (assuming a spherical earth)
            coursediff_rad = math.radians(course_p_self - course_p_q)
            dist_p_self_rad = dist_p_self / Util.r_earth
            dist_rad = math.asin(math.sin(dist_p_self_rad) * math.sin(coursediff_rad))
            return Util.r_earth * dist_rad

    def course (self, p):
        """
        initial course [degrees] to reach c from self on a great circle

        range of returned values:
        -180 < course <= 180
        (-90 = west, 0 = north, 90 = east, 180 = south)
        """
        if not isinstance(p, LatLon):
            raise TypeError("argument must be of class LatLon")
        return Util.course(self.lat, self.lon, p.lat, p.lon)

    def angle (self, p, q):
        """
        return angle [degrees] between p and q, as seen from self

        range of returned values: -180 < angle <= 180
        positive: q is "right of p"
        negative: q is "left of p"
        """
        res = (course(self,q) - course(self,p)) % 360
        if res > 180:
            res -= 180
        return res

    def transMercator (self, centerlon=0.0):
        """
        transversal Mercator projection - returns (x,y) tuple (unit: m)

        centerlon = longitude [degrees] of central meridian (x=0)
        """
        return Util.transMercator(self.lat, self.lon, centerlon)

    def __eq__ (self, c):
        return (self.__class__ == c.__class__ and self._lat == p._lat and self._lon == p._lon)

    def __ne__ (self, c):
        return not (self == c)

    def __hash__ (self):
        return hash((self._lat, self._lon))

    def __neg__ (self):
        """
        return antipodal point of self
        """
        return LatLon(-self._lat, self._lon+180)

    def __add__ (self, gv):
        if not isinstance(gv, CourseDistance):
            raise TypeError("argument must be of class CourseDistance")
        lat, lon = Util.endPosition(self.lat, self.lon, gv.course, gv.distance)
        return LatLon(lat, lon)

    def __radd__ (self, gv):
        if not isinstance(gv, CourseDistance):
            raise TypeError("argument must be of class CourseDistance")
        lat, lon = Util.endPosition(self.lat, self.lon, gv.course, gv.distance)
        return LatLon(lat, lon)

    def __iadd__ (self, gv):
        if not isinstance(gv, CourseDistance):
            raise TypeError("argument must be of class CourseDistance")
        self._lat, self._lon = LatLon(Util.endPosition(self.lat, self.lon, gv.course, gv.distance))
        return self

    def __rsub__ (self, c):
        if not isinstance(c, LatLon):
            raise TypeError("argument must be of class LatLon")
        course, distance = Util.courseAndDistance(self.lat, self.lon, c.lat, c.lon)
        return CourseDistance(course, distance)

    def __sub__ (self, x):
        if isinstance(x, LatLon):
            return x.__rsub__(self)
        elif isinstance(x, CourseDistance):
            return self + -x
        else:
            raise TypeError("argument must be of class LatLon or CourseDistance")

    def __isub__ (self, gv):
        if not isinstance(x, CourseDistance):
            raise TypeError("argument must be of class CourseDistance")
        self._lat, self._lon = LatLon(Util.endPosition(self.lat, self.lon, gv.course+180, gv.distance))
        return self

# some static constants

LatLon.northPole = LatLon(90, 0)
LatLon.southPole = LatLon(-90, 0)

# ----------------------------------------

class CourseDistance:
    """
    Representation of a movement by a certain distance along a great circle.

    Properties:
    course    initial course [degrees]  (-180 < course <= 180)
              (-90 = west, 0 = north, 90 = east, 180 = south)
    distance  traveled distance [m]     (always >= 0)

    Constructor:
    CourseDistance(course, distance)
    """
    @property
    def course(self):
        """
        initial course [degrees]

        range: -180 < course <= 180
        -90 = west, 0 = north, 90 = east, 180 = south
        """
        return self._course

    @property
    def distance(self):
        """
        traveled distance [m]
        """
        return self._distance

    def __init__(self, course, distance):
        # normalize distance to non-negative values
        if distance < 0:
            distance = -distance
            course += 180
        # normalize course to the interval ]-180,180]
        self._course = float(course) % 360
        if self._course > 180:
            self._course -= 360
        self._distance = float(distance)

    @staticmethod
    def north(distance):
        """
        returns a movement by a certain distance to the north
        """
        return CourseDistance(0, distance)

    @staticmethod
    def east(distance):
        """
        returns a movement by a certain distance with inital direction east
        """
        return CourseDistance(90, distance)

    @staticmethod
    def south(distance):
        """
        returns a movement by a certain distance to the south
        """
        return CourseDistance(180, distance)

    @staticmethod
    def west(distance):
        """
        returns a movement by a certain distance with inital direction west
        """
        return CourseDistance(-90, distance)

    def __repr__ (self):
        return "".join(["CourseDistance(", repr(self._course), ",", repr(self._distance), ")"])

    def __str__ (self):
        return "".join(["CourseDistance(", str(self._course), ",", str(self._distance), ")"])

    def __eq__ (self, c):
        return (self.__class__ == c.__class__ and self._course == p._course and self._distance == p._distance)

    def __ne__ (self, c):
        return not (self == c)

    def __hash__ (self):
        return hash((self._course, self._distance))

    def __neg__ (self):
        """
        returns a movement by the same distance into the opposite direction
        """
        return CourseDistance(self._course+180, self._distance)

    def __mul__ (self, factor):
        """
        returns a movement by a multiple of the original distance into the same direction
        """
        return CourseDistance(self._course, self._distance * float(factor))

    def __rmul__ (self, factor):
        """
        returns a movement by a multiple of the original distance into the same direction
        """
        return CourseDistance(self._course, self._distance * float(factor))

    def __div__ (self, factor):
        """
        returns a movement by a fraction of the original distance into the same direction
        """
        return CourseDistance(self._course, self._distance / float(factor))

    def __truediv__ (self, factor):
        """
        returns a movement by a fraction of the original distance into the same direction
        """
        return CourseDistance(self._course, self._distance / float(factor))

# ----------------------------------------

class Document:
    """
    Representation of a GPX document

    Constructor:
    Document(children=[], name="(unnamed)")

    The parameter "children" can be any iterable of Tracks, Routes and/or Waypoints.

    Note: the interface was changed in version 1.2.0, replacing the parameters "tracks" and "waypoints" by "children"
    """

    def __init__ (self, children=None, name="(unnamed)"):
        self.tracks = []
        self.routes = []
        self.waypoints = []
        for child in children:
            self.append(child)
        self.name = name

    def __str__ (self):
        return ('<Document "%s" (%d tracks, %d routes, %d waypoints)>' %
                (self.name, len(self.tracks), len(self.routes), len(self.waypoints)))

    def __repr__ (self):
        s = [ 'Document(', repr(self.tracks), ',', repr(self.routes), ',', repr(self.waypoints),
              ',', repr(self.name), ')' ]
        return ''.join(s)

    def append (self, child):
        """
        append a Track, Route, or Waypoint to this Document
        """
        if isinstance(child, Track):
            self.tracks.append(child)
        elif isinstance(child, Route):
            self.routes.append(child)
        elif isinstance(child, Waypoint):
            self.waypoints.append(child)
        else:
            raise TypeError

    def toGPX (self, domImpl=getDOMImplementation()):
        """
        convert to GPX DOM
        """
        doc = domImpl.createDocument ("http://www.topografix.com/GPX/1/1","gpx",None)
        gpx = doc.documentElement
        gpx.setAttribute ("xmlns","http://www.topografix.com/GPX/1/1")
        gpx.setAttribute ("creator", "")
        gpx.setAttribute ("version", "1.1")
        gpx.setAttribute ("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
        gpx.setAttribute ("xsi:schemaLocation", "http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd")
        for trk in self.tracks:
            gpx.appendChild (trk.toGPX(doc))
        for rte in self.routes:
            gpx.appendChild (rte.toGPX(doc))
        for wpt in self.waypoints:
            gpx.appendChild (wpt.toGPX(doc))
        return doc

    def writeGPX (self, file, encoding='utf-8'):
        """
        write GPX file
        """
        if isinstance (file, basestring):
            self.writeGPX (open (file, 'wb'), encoding)
            return
        gpx = self.toGPX (getDOMImplementation())
        Util.writexml (gpx, file, encoding)

    @staticmethod
    def fromGPX (dom, name='(unnamed)'):
        """
        parse GPX DOM
        """
        children = []
        for trk in dom.getElementsByTagName("trk"):
            children.append (Track.fromGPX (trk))
        for rte in dom.getElementsByTagName("rte"):
            children.append (Route.fromGPX (rte))
        for wpt in dom.getElementsByTagName("wpt"):
            children.append (Waypoint.fromGPX (wpt))
        return Document (children, name)

    @staticmethod
    def readGPX (file, name='(unnamed)'):
        """
        read GPX file
        """
        dom = parse(file)
        return Document.fromGPX (dom, name)

    # create KML document
    def toKML (self, domImpl):
        """
        convert to KML DOM
        """
        doc = domImpl.createDocument ("http://earth.google.com/kml/2.0","kml",None)
        kml = doc.documentElement
        kml.setAttribute ("xmlns","http://earth.google.com/kml/2.0")

        # create Document tag
        document = doc.createElement("Document")
        kml.appendChild(document)
        document.setAttribute ("xmlns","http://earth.google.com/kml/2.0")
        e = doc.createElement("name")
        e.appendChild (doc.createTextNode(self.name))
        document.appendChild (e)
        e = doc.createElement ("visibility")
        e.appendChild (doc.createTextNode("1"))
        document.appendChild (e)

        # create Tracks folder
        trkfolder = doc.createElement ("Folder")
        document.appendChild (trkfolder)
        e = doc.createElement ("name")
        e.appendChild (doc.createTextNode("Tracks"))
        trkfolder.appendChild (e)

        # append tracks
        for trk in self.tracks:
            trkfolder.appendChild (trk.toKML(doc))

        # create Routes folder
        rtefolder = doc.createElement ("Folder")
        document.appendChild (rtefolder)
        e = doc.createElement ("name")
        e.appendChild (doc.createTextNode("Routes"))
        rtefolder.appendChild (e)

        # append routes
        for rte in self.routes:
            rtefolder.appendChild (rte.toKML(doc))

        # create Waypoints folder
        wptfolder = doc.createElement ("Folder")
        document.appendChild (wptfolder)
        e = doc.createElement ("name")
        e.appendChild (doc.createTextNode("Waypoints"))
        wptfolder.appendChild (e)

        # append waypoints
        for wpt in self.waypoints:
            wptfolder.appendChild (wpt.toKML(doc))

        return doc

    def writeKML (self, file, encoding='utf-8'):
        """
        write KML file
        """
        if isinstance (file, basestring):
            self.writeKML (open (file, 'wb'), encoding)
            return
        kml = self.toKML (getDOMImplementation())
        Util.writexml (kml, file, encoding)

    @staticmethod
    def fromKML (dom):
        """
        parse KML DOM
        """
        doc = dom.getElementsByTagName('Document')[0]
        name = '(unnamed)'
        for e in doc.getElementsByTagName('name'):
            name = e.childNodes[0].data.strip()
        children = []
        for placemark in doc.getElementsByTagName("Placemark"):
            if len (placemark.getElementsByTagName ("LineString")) > 0:
                children.append (Track.fromKML (placemark))
            elif len (placemark.getElementsByTagName ("Point")) > 0:
                children.append (Waypoint.fromKML (placemark))
        return Document (children, name)

    @staticmethod
    def readKML (file):
        """
        read KML file
        """
        dom = parse(file)
        return Document.fromKML (dom)

    def toOVL (self, ostream):
        """
        write OVL to output stream
        """
        groupnr = 0
        symbolnr = 0
        bmin, bmax = 100.0, -100.0
        lmin, lmax = 200.0, -200.0
        for track in self.tracks:
            groupnr = groupnr+1
            segnr = 0
            for trkseg in track.segments:
                symbolnr = symbolnr+1
                ostream.write (
                    "[Symbol %d]\r\n"
                    "Typ=3\r\n"
                    "Group=%d\r\n"
                    "Col=1\r\n"
                    "Zoom=1\r\n"
                    "Size=103\r\n"
                    "Art=1\r\n"
                    % (symbolnr, groupnr))
                punkte = trkseg.points
                ostream.write ("Punkte=%d\r\n" % len(punkte))
                punktnr = 0
                for trkpt in punkte:
                    b = float(trkpt.lat)
                    l = float(trkpt.lon)
                    bmin, bmax = min (bmin, b), max (bmax, b)
                    lmin, lmax = min (lmin, l), max (lmax, l)
                    ostream.write ("XKoord%d=%.6f\r\n" % (punktnr, l))
                    ostream.write ("YKoord%d=%.6f\r\n" % (punktnr, b))
                    punktnr = punktnr+1
        for route in self.routes:
            groupnr = groupnr+1
            symbolnr = symbolnr+1
            ostream.write (
                "[Symbol %d]\r\n"
                "Typ=3\r\n"
                "Group=%d\r\n"
                "Col=1\r\n"
                "Zoom=1\r\n"
                "Size=103\r\n"
                "Art=1\r\n"
                % (symbolnr, groupnr))
            punkte = route.points
            ostream.write ("Punkte=%d\r\n" % len(punkte))
            punktnr = 0
            for rtept in punkte:
                b = float(rtept.lat)
                l = float(rtept.lon)
                bmin, bmax = min (bmin, b), max (bmax, b)
                lmin, lmax = min (lmin, l), max (lmax, l)
                ostream.write ("XKoord%d=%.6f\r\n" % (punktnr, l))
                ostream.write ("YKoord%d=%.6f\r\n" % (punktnr, b))
                punktnr = punktnr+1
        groupnr = groupnr+1
        for waypoint in self.waypoints:
            symbolnr = symbolnr+1
            ostream.write (
                "[Symbol %d]\r\n"
                "Typ=6\r\n"
                "Group=%d\r\n"
                "Width=10\r\n"
                "Height=10\r\n"
                "Dir=100\r\n"
                "Col=1\r\n"
                "Zoom=1\r\n"
                "Size=103\r\n"
                "Area=2\r\n"
                "XKoord=%.6f\r\n"
                "YKoord=%.6f\r\n"
                % (symbolnr, groupnr, waypoint.lon, waypoint.lat))
        ostream.write (
            "[Overlay]\r\n"
            "Symbols=%d\r\n"
            "[MapLage]\r\n"
            "MapName=Top. Karte 1:50000 Bw\r\n"
            "DimmFc=100\r\n"
            "ZoomFc=100\r\n"
            "CenterLat=%.6f\r\n"
            "CenterLong=%.6f\r\n"
            "RefOn=0\r\n"
            % (symbolnr, (bmin+bmax)/2, (lmin+lmax)/2))

    def writeOVL (self, file, encoding='iso-8859-1'):
        """
        write OVL file
        """
        if isinstance (file, basestring):
            self.toOVL (codecs.open (file, 'w', encoding), encoding)
        else:
            self.toOVL (codecs.getwriter (encoding)(file))

    @staticmethod
    def fromOVL (istream, name="(unnamed)"):
        """
        parse OVL from input stream
        """
        tracks = {} # Map Group -> Track

        mode = "start"
        for line in istream:
            if line.startswith("["):
                if mode == "symbol":
                    # Group schon vorhanden?
                    if symbolGroup in tracks:
                        track = tracks[symbolGroup]
                    else:
                        track = Track ("%s/%d" % (name, symbolGroup))
                        tracks[symbolGroup] = track
                    # Symbol schreiben
                    trkseg = TrackSegment()
                    for lon, lat in koord:
                        trkpt = TrackPoint (lat, lon)
                        trkseg.appendPoint (trkpt)
                    track.appendSegment (trkseg)
                if line.startswith("[Symbol"):
                    symbolTyp = None
                    symbolGroup = None
                    koord = []
                    mode = "symbol"
                else:
                    mode = "other"
            elif line.startswith ("Group"):
                symbolGroup = int(line.strip().split("=")[1])
            elif line.startswith ("XKoord"):
                x = float(line.strip().split("=")[1])
            elif line.startswith ("YKoord"):
                y = float(line.strip().split("=")[1])
                koord.append ((x, y))

        groups = sorted(tracks.keys())
        return Document([tracks[group] for group in groups], name=name)

    @staticmethod
    def readOVL (file, name='(unnamed)', encoding='iso-8859-1'):
        """
        read OVL file
        """
        if isinstance (file, basestring):
            return Document.fromOVL (codecs.open (file, 'r', encoding), basename(file))
        else:
            return Document.fromOVL (codecs.getreader (encoding)(file), basename(file.name))

# ----------------------------------------
# Representation of a GPX track
# ----------------------------------------
class Track:
    """
    Representation of a GPX track

    Constructor:
    Track(name=None, description=None, segments=[], **kwargs)
    keyword arguments: commment, source, number, type
    """

    _attributes = ["comment", "source", "number", "type"]
    """
    list of additional attributes
    """
    # TODO: missing attributes: link, extensions

    def __init__ (self, name=None, description=None, segments=None, **kwargs):
        self.name = name
        self.description = description
        if segments == None:
            self.segments = []
        else:
            # segments must be an iterable whose items can be cast to TrackSegment
            self.segments = [ TrackSegment.cast(seg) for seg in segments ]
        # process additional arguments
        for keyword in self._attributes:
            if keyword in kwargs:
                setattr(self, keyword, kwargs[keyword])
            else:
                setattr(self, keyword, None)

    @staticmethod
    def cast (object):
        """
        try to cast an object to a Track instance
        """
        if isinstance(object, Track):
            return object
        elif hasattr(object, "__iter__"):
            # the object is iterable - try to cast its items to TrackSegments
            res = Track(segments=object)
            # copy attributes
            for attr in ["name", "description"] + cls._attributes:
                if hasattr(obj, attr):
                    setattr(res, attr, getattr(obj, attr))
            return res
        else:
            raise TypeError

    def __str__ (self):
        return '<Track "%s" (%d segments)>' % (self.name, len(self.segments))

    def __repr__ (self):
        s = [ 'Track(', repr(self.name), ',', repr(self.description), ',', repr(self.segments) ]
        for a in self._attributes:
            value = getattr(self, a)
            if value != None:
                s.extend([',', a, "=", repr(value)])
        s.append(')')
        return ''.join(s)

    def __iter__ (self):
        """
        iterate over all track segments
        """
        return self.segments.__iter__()

    def _len__ (self):
        """
        return number of track segments
        """
        return len(self.segments)

    def __getitem__ (self, i):
        """
        return i-th track segment
        """
        return self.segments[i]

    def append (self, trkseg):
        """
        append a track segment to this track
        """
        self.segments.append(TrackSegment.cast(trkseg))

    def extend (self, trk):
        """
        append a list of track segments to this track
        """
        self.segments.extend ([TrackSegment.cast(s) for s in trk])

    def appendSegment (self, trkseg):
        warnings.warn("appendSegment() is deprecated - use append() instead", DeprecationWarning)
        self.append(trkseg)

    def appendTrack (self, trk):
        warnings.warn("appendTrack() is deprecated - use extend() instead", DeprecationWarning)
        self.extend(trk)

    def length (self):
        """
        total length of all segments [m]
        """
        l = 0.0
        for s in self.segments:
            l += s.length()
        return l

    def boundingBox (self):
        """
        return minimum/maximum coordinates of this track
        as tuple (minLat, minLon, maxLat, maxLon)
        """
        minLat = minLon = maxLat = maxLon = None
        first = True
        for segment in self.segments:
            try:
                s_minLat, s_minLon, s_maxLat, s_maxLon = segment.boundingBox()
            except ValueError: # segment is empty
                continue
            if first:
                minLat, minLon, maxLat, maxLon = s_minLat, s_minLon, s_maxLat, s_maxLon
                first = False
            else:
                minLat = min(minLat, s_minLat)
                minLon = min(minLon, s_minLon)
                maxLat = max(maxLat, s_maxLat)
                maxLon = max(maxLon, s_maxLon)
        if first:
            raise ValueError("empty track has no bounding box")
        return minLat, minLon, maxLat, maxLon

    def transMercator (self, centerlon=0.0):
        """
        Transversal Mercator projection - returns list of lists of (x,y) tuples (unit: m)

        Each sub-list corresponds to a track segment.
        """
        return [ s.transMercator(centerlon) for s in self.segments ]

    def toGPX (self, doc):
        """
        convert to GPX Element <trk>
        """
        res = doc.createElement("trk")
        if self.name != None:
            e = doc.createElement("name")
            e.appendChild (doc.createTextNode(self.name))
            res.appendChild (e)
        if self.comment != None:
            e = doc.createElement("cmt")
            e.appendChild (doc.createTextNode(self.comment))
            res.appendChild (e)
        if self.description != None:
            e = doc.createElement("desc")
            e.appendChild (doc.createTextNode(self.description))
            res.appendChild (e)
        if self.source != None:
            e = doc.createElement("src")
            e.appendChild (doc.createTextNode(self.source))
            res.appendChild (e)
        if self.number != None:
            e = doc.createElement("number")
            e.appendChild (doc.createTextNode(repr(self.number)))
            res.appendChild (e)
        if self.type != None:
            e = doc.createElement("type")
            e.appendChild (doc.createTextNode(self.type))
            res.appendChild (e)
        for p in self.segments:
            res.appendChild (p.toGPX (doc))
        return res

    @staticmethod
    def fromGPX (trk):
        "parse GPX Element <trk>"
        name = None
        for e in trk.getElementsByTagName("name"):
            name = e.childNodes[0].data.strip()
        comment = None
        for e in trk.getElementsByTagName("cmt"):
            comment = e.childNodes[0].data.strip()
        description = None
        for e in trk.getElementsByTagName("desc"):
            description = e.childNodes[0].data.strip()
        source = None
        for e in trk.getElementsByTagName("src"):
            source = e.childNodes[0].data.strip()
        number = None
        for e in trk.getElementsByTagName("number"):
            number = int(e.childNodes[0].data)
        type = None
        for e in trk.getElementsByTagName("type"):
            type = int(e.childNodes[0].data)
        res = Track (name, description, segments=[],
                     comment=comment, source=source, number=number, type=type)
        for trkseg in trk.getElementsByTagName("trkseg"):
            res.append(TrackSegment.fromGPX (trkseg))
        return res

    def toKML (self, doc):
        """
        convert to KML Element <Placemark>
        """
        res = doc.createElement("Placemark")
        if self.name != None:
            e = doc.createElement("name")
            e.appendChild (doc.createTextNode(self.name))
            res.appendChild (e)
        if self.description != None:
            e = doc.createElement("description")
            e.appendChild (doc.createTextNode(self.description))
            res.appendChild (e)
        for p in self.segments:
            res.appendChild (p.toKML (doc))
        return res

    @staticmethod
    def fromKML (placemark):
        """
        parse KML Element <Placemark>
        """
        name = "(unnamed)"
        for e in placemark.getElementsByTagName ("name"):
            name = e.childNodes[0].data.strip()
        track = Track(name)
        for e in placemark.getElementsByTagName ("LineString"):
            track.appendSegment (TrackSegment.fromKML (e))
        return track

# ----------------------------------------

class LineString:
    """
    Representation of a list of points (abstract base class for TrackSegment and Route)

    Constructor:
    no constructor because class is abstract
    """

    def __str__ (self):
        return '<%s (%d points)>' % (self.__class__.__name__, len(self.points))

    def __repr__ (self):
        s = [ self.__class__.__name__,  '(', repr(self.points), ')' ]
        return "".join(s)

    def __getitem__ (self, i):
        return self.points[i]

    def __len__ (self):
        return len(self.points)

    def __iter__ (self):
        return self.points.__iter__

    def append (self, point):
        self.points.append(point)

    def extend (self, linestring):
        self.points.extend(linestring.points)

    def appendPoint (self, point):
        warnings.warn("appendPoint() is deprecated - use append() instead", DeprecationWarning)
        self.append(point)

    def __iadd__ (self, linestring):
        if self.__class__ != linestring.__class__:
            linestring = self.__class__ (linestring)
        self.points += linestring.points

    def __add_ (self, linestring):
        return self.__class__ (self.points + linestring.points)

    def __iter__ (self):
        return self.points.__iter__()

    def length (self):
        """
        length of track segment or route [m]
        """
        l = 0.0
        for i in range(len(self.points)-1):
            l += self.points[i].distance(self.points[i+1])
        return l

    def boundingBox (self):
        """
        return minimum/maximum coordinates of this LineString
        as tuple (minLat, minLon, maxLat, maxLon)
        """
        if len(self.points) == 0:
            raise ValueError("empty track segment has no bounding box")
        minLat = maxLat = self.points[0].lat
        minLon = maxLon = self.points[0].lon
        for p in self.points[1:]:
            minLat = min(minLat, p.lat)
            minLon = min(minLon, p.lon)
            maxLat = max(maxLat, p.lat)
            maxLon = max(maxLon, p.lon)
        return minLat, minLon, maxLat, maxLon

    def atDistance (self, distance):
        """
        return the Point at a given distance [m] from the stating point of the LineString
        """
        if distance < 0.0:
            raise ValueError("cannot interpolate beyond start of LineString")
        l = 0.0
        for i in range(len(self.points)-1):
            p_i = self.points[i]
            p_i1 = self.points[i+1]
            d = p_i.distance(p_i1)
            if distance >= l and distance <= l+d:
                # linear interpolation between points[i] and points[i+1]
                ratio = (distance-l) / d
                lat, lon = Util.interpolate(p_i.lat, p_i.lon, p_i1.lat, p_i1.lon, ratio)
                p = Point(lat, lon)
                if p_i.ele != None and p_i1.ele != None:
                    p.ele = p_i.ele + ratio * (p_i1.ele - p_i.ele)
                if p_i.t != None and p_i1.t != None:
                    sec = ratio * (p_i1.t - p_i.t).total_seconds()
                    p.t = p_i.t + datetime.timedelta(seconds=sec)
                return p
            l += d
        raise ValueError("cannot interpolate beyond end of LineString")

    def transMercator (self, centerlon=0.0):
        """
        Transversal Mercator projection - returns list of (x,y) tuples (unit: m)
        """
        return [ p.transMercator(centerlon) for p in self.points ]

    def simplify (self, delta=1.0):
        """
        Reduce number of track points while preserving the shape of the track segment as much as possible.

        The parameter delta gives the minimum distance [m] that a track point should have
        from the straight line connecting its predecessor and successor.
        """
        n = len(self.points)
        if n <= 2:
            # there's nothing to simplify
            return
        idx = [0] + self._simplify (0, n-1, delta) + [n-1]
        self.points = [ self.points[i] for i in idx ]

    def _simplify (self, start, end, delta):
        # Reduce number of intermediate points between points[start] and points[end]
        if end-start <= 1:
            return [] # there are no intermediate points
        # calculate the point with maximum distance
        # from the straight line between points[start] and points[end]
        max_dist =  0.0
        max_index = None
        for k in range(start+1, end):
            d = self.points[k].distance (self.points[start], self.points[end])
            if d > max_dist:
                max_dist = d
                max_index = k
        if max_dist < delta:
            return [] # discard all intermediate points
        # recursion
        return (
            self._simplify(start, max_index, delta)
            + [max_index]
            + self._simplify(max_index, end, delta))

    def toKML (self, doc):
        """
        convert to KML Element <LineString>
        """
        res = doc.createElement ("LineString")
        coord = doc.createElement ("coordinates")
        coordStr = " ".join([p.toKML(doc) for p in self.points])
        coord.appendChild (doc.createTextNode (coordStr))
        res.appendChild (coord)
        return res

# ----------------------------------------
# Representation of a GPX track segment
# ----------------------------------------
class TrackSegment(LineString):
    """
    Representation of a GPX track segment

    Constructor:
    TrackSegment(points=[])
    """

    def __init__ (self, points=None):
        if points == None:
            self.points = []
        else:
            # points must be an iterable whose items can be cast to TrackPoint
            self.points = [ TrackPoint.cast(p) for p in points ]

    @staticmethod
    def cast (obj):
        """
        try to cast an object to a TrackSegment
        """
        if isinstance(obj, TrackSegment):
            return obj
        elif hasattr(obj, "__iter__"):
            # the object is iterable - try to cast its items to TrackPoints
            return TrackSegment(points=obj)
        else:
            raise TypeError

    def append (self, point):
        self.points.append(TrackPoint.cast(point))

    def extend (self, linestring):
        self.points.extend([TrackPoint.cast(p) for p in linestring])

    def toGPX (self, doc):
        """
        convert to GPX Element <trkseg>
        """
        res = doc.createElement("trkseg")
        for p in self.points:
            res.appendChild (p.toGPX (doc))
        return res

    @staticmethod
    def fromGPX (trkseg):
        """
        parse GPX Element <trkseg>
        """
        res = TrackSegment()
        for trkpt in trkseg.getElementsByTagName("trkpt"):
            res.appendPoint (TrackPoint.fromGPX (trkpt))
        return res

    @staticmethod
    def fromKML (linestring):
        """
        parse KML Element <LineString>
        """
        trkseg = TrackSegment()
        coords = linestring.getElementsByTagName("coordinates")[0].childNodes[0].data.strip()
        for c in coords.split ():
            lon, lat, ele = c.split (",")
            lon = float(lon)
            lat = float(lat)
            if ele == "0":
                ele = None
            else:
                ele = float(ele)
            trkseg.appendPoint (TrackPoint (lon, lat, ele))
        return trkseg

# ----------------------------------------

class Route(LineString):
    """
    Representation of a GPX route

    Constructor:
    Route(name=None, description=None, points=[], **kwargs)
    keyword arguments: commment, source, number, type
    """

    _attributes = ["comment", "source", "number", "type"]
    """
    list of additional attributes
    """
    # TODO: missing attributes: link, extensions

    def __init__ (self, name=None, description=None, points=None, **kwargs):
        self.name = name
        self.description = description
        if points == None:
            self.points = []
        else:
            # points must be an iterable whose items can be cast to TrackPoint
            self.points = [ RoutePoint.cast(p) for p in points ]
        # process additional arguments
        for keyword in self._attributes:
            if keyword in kwargs:
                setattr(self, keyword, kwargs[keyword])
            else:
                setattr(self, keyword, None)

    @classmethod
    def cast (cls, obj):
        """
        try to cast an object to a Route
        """
        if isinstance(obj, cls):
            return obj
        elif hasattr(obj, "__iter__"):
            # the object is iterable - try to cast its items to RoutePoints
            res = Route(points=obj)
            # copy attributes
            for attr in ["name", "description"] + cls._attributes:
                if hasattr(obj, attr):
                    setattr(res, attr, getattr(obj, attr))
            return res
        else:
            raise TypeError

    def append (self, point):
        self.points.append(RoutePoint.cast(point))

    def extend (self, linestring):
        self.points.extend([RoutePoint.cast(p) for p in linestring])

    def toGPX (self, doc):
        """
        convert to GPX Element <rte>
        """
        res = doc.createElement("rte")
        if self.name != None:
            e = doc.createElement("name")
            e.appendChild (doc.createTextNode(self.name))
            res.appendChild (e)
        if self.comment != None:
            e = doc.createElement("cmt")
            e.appendChild (doc.createTextNode(self.comment))
            res.appendChild (e)
        if self.description != None:
            e = doc.createElement("desc")
            e.appendChild (doc.createTextNode(self.description))
            res.appendChild (e)
        if self.source != None:
            e = doc.createElement("src")
            e.appendChild (doc.createTextNode(self.source))
            res.appendChild (e)
        if self.number != None:
            e = doc.createElement("number")
            e.appendChild (doc.createTextNode(repr(self.number)))
            res.appendChild (e)
        if self.type != None:
            e = doc.createElement("type")
            e.appendChild (doc.createTextNode(self.type))
            res.appendChild (e)
        for p in self.points:
            res.appendChild (p.toGPX (doc))
        return res

    @staticmethod
    def fromGPX (rte):
        """
        parse GPX Element <rte>
        """
        name = None
        for e in rte.getElementsByTagName("name"):
            name = e.childNodes[0].data.strip()
        comment = None
        for e in rte.getElementsByTagName("cmt"):
            comment = e.childNodes[0].data.strip()
        description = None
        for e in rte.getElementsByTagName("desc"):
            description = e.childNodes[0].data.strip()
        source = None
        for e in rte.getElementsByTagName("src"):
            source = e.childNodes[0].data.strip()
        number = None
        for e in rte.getElementsByTagName("number"):
            number = int(e.childNodes[0].data)
        type = None
        for e in rte.getElementsByTagName("type"):
            type = int(e.childNodes[0].data)
        points = []
        res = Route(name, description, points=[],
                    comment=comment, source=source, number=number, type=type)
        for rtept in rte.getElementsByTagName("rtept"):
            res.append(RoutePoint.fromGPX (rtept))
        return res

    def toKML (self, doc):
        """
        convert to KML Element <Placemark>
        """
        res = doc.createElement ("Placemark")
        if self.name != None:
            e = doc.createElement("name")
            e.appendChild (doc.createTextNode(self.name))
            res.appendChild (e)
        if self.description != None:
            e = doc.createElement("description")
            e.appendChild (doc.createTextNode(self.description))
            res.appendChild (e)
        linestring = doc.createElement ("LineString")
        coord = doc.createElement ("coordinates")
        coordStr = " ".join([p.toKML(doc) for p in self.points])
        coord.appendChild (doc.createTextNode (coordStr))
        linestring.appendChild (coord)
        res.appendChild (linestring)
        return res

# ----------------------------------------
# Common base class for track points, route points and waypoints
# ----------------------------------------
class Point(LatLon):
    """
    Common base class for track points (class TrackPoint), route points (class RoutePoint)
    and waypoints (class Waypoint)

    Constructor: Point(lat, lon, ele=None, t=None, name=None)
    """

    def __init__ (self, lat, lon, ele=None, t=None, name=None):
        LatLon.__init__(self, lat, lon)
        self.ele = ele
        self.t = t
        self.name = name

    def __str__ (self):
        s = [ self.__class__.__name__, '(', str(self._lat), ',', str(self._lon) ]
        if self.ele != None:
            s += [ ',ele=', str(self.ele) ]
        if self.t != None:
            s += [ ',t=', str(self.t) ]
        if self.name != None:
            s += [ ',name=', unicode(self.name) ]
        s.append(')')
        return ''.join(s)

    def __repr__ (self):
        s = [ self.__class__.__name__, '(', repr(self._lat), ',', repr(self._lon),
              ',',  repr(self.ele), ',', repr(self.t), ',', repr(self.name), ')' ]
        return ''.join(s)

    def __eq__ (self, p):
        return (
            self.__class__ == p.__class__
            and self._lat == p._lat and self._lon == p._lon
            and self.ele == p.ele and self.t == p.t
            and self.name == p.name)

    def __ne__ (self, p):
        return not (self == p)

    def __hash__ (self):
        return hash((self.lat, self.lon, self.ele, self.t, self.name))

    @classmethod
    def cast (cls, obj):
        """
        try to cast an object to class cls (which is a subclass of Point)
        """
        if isinstance (obj, cls):
            return obj
        elif isinstance (obj, LatLon):
            p = cls(obj.lat, obj.lon)
            if hasattr(obj, "ele"):
                p.ele = obj.ele
            if hasattr(obj, "t"):
                p.t = obj.t
            if hasattr(obj, "name"):
                p.name = obj.name
            return p
        else:
            raise TypeError

    def _toGPX (self, doc, elementName):
        """
        convert to GPX Element (called by the toGPX() methods of subclasses)
        """
        res = doc.createElement(elementName)
        res.setAttribute ("lat", ("%.6f" % self.lat))
        res.setAttribute ("lon", ("%.6f" % self.lon))
        if self.name != None:
            e = doc.createElement("name")
            e.appendChild (doc.createTextNode(self.name))
            res.appendChild (e)
        if self.ele != None:
            e = doc.createElement("ele")
            e.appendChild (doc.createTextNode(str(self.ele)))
            res.appendChild (e)
        if self.t != None:
            e = doc.createElement("time")
            t = self.t.strftime ("%Y-%m-%dT%H:%M:%SZ")
            e.appendChild (doc.createTextNode(t))
            res.appendChild (e)
        return res

    @classmethod
    def fromGPX (cls, element):
        """
        parse GPX Element <wpt>, <trkpt> or <rtept>
        """
        lat = float(element.getAttribute("lat"))
        lon = float(element.getAttribute("lon"))
        name = None
        for e in element.getElementsByTagName("name"):
            name = e.childNodes[0].data.strip()
        ele = None
        for e in element.getElementsByTagName("ele"):
            ele = float(e.childNodes[0].data.strip())
        t = None
        for e in element.getElementsByTagName("time"):
            t = dateutil.parser.parse (e.childNodes[0].data.strip())
        return cls (lat, lon, ele, t, name)

# ----------------------------------------
# Representation of a GPX track point
# ----------------------------------------
class TrackPoint(Point):
    """
    Representation of a GPX track point

    Constructor: TrackPoint(lat, lon, ele=None, t=None, name=None)
    """

    def toGPX (self, doc):
        """
        convert to GPX Element <trkpt>
        """
        return Point._toGPX(self, doc, "trkpt")

    def toKML (self, doc):
        """
        convert to KML-formatted coordinate string
        """
        if self.ele is None:
            return "%f,%f,0" % (self.lon, self.lat)
        else:
            return "%f,%f,%.3f" % (self.lon, self.lat, self.ele)

# ----------------------------------------
# Representation of a GPX route point
# ----------------------------------------
class RoutePoint(Point):
    """
    Representation of a GPX route point

    Constructor: RoutePoint(lat, lon, ele=None, t=None, name=None)
    """

    def toGPX (self, doc):
        """
        convert to GPX Element <wpt>
        """
        return Point._toGPX(self, doc, "rtept")

    def toKML (self, doc):
        """
        convert to KML-formatted coordinate string
        """
        if self.ele is None:
            return "%f,%f,0" % (self.lon, self.lat)
        else:
            return "%f,%f,%.3f" % (self.lon, self.lat, self.ele)

# ----------------------------------------
# Representation of a GPX waypoint
# ----------------------------------------
class Waypoint(Point):
    """
    Representation of a GPX waypoint

    Constructor: Waypoint(lat, lon, ele=None, t=None, name=None)

    Note: the order of constructor parameters has changed in version 1.2.0
    (name is now last) to be consistent with TrackPoint and RoutePoint
    """

    def toGPX (self, doc):
        """
        convert to GPX Element <wpt>
        """
        return Point._toGPX(self, doc, "wpt")

    def toKML (self, doc):
        """
        convert to KML Element <Placemark>
        """
        res = doc.createElement ("Placemark")
        if self.name != None:
            e = doc.createElement ("name")
            e.appendChild (doc.createTextNode (self.name))
            res.appendChild (e)
        if self.t != None:
            ts = doc.createElement ("TimeStamp")
            e = doc.createElement ("when")
            e.appendChild (doc.createTextNode (self.t.strftime ("%Y-%m-%dT%H:%M:%SZ")))
            ts.appendChild (e)
            res.appendChild (ts)
        p = doc.createElement ("Point")
        c = doc.createElement ("coordinates")
        if self.ele is None:
            coords = "%f,%f,0" % (self.lon, self.lat)
        else:
            coords = "%f,%f,%.3f" % (self.lon, self.lat, self.ele)
        c.appendChild (doc.createTextNode (coords))
        p.appendChild (c)
        res.appendChild (p)
        return res

    @staticmethod
    def fromKML (placemark):
        """
        parse KML Element <Placemark>
        """
        name = "(unnamed)"
        for e in placemark.getElementsByTagName ("name"):
            name = e.childNodes[0].data.strip()
        for p in placemark.getElementsByTagName ("Point"):
            coords = p.getElementsByTagName("coordinates")[0].childNodes[0].data.strip()
            lon, lat, ele = coords.split (",")
            lon = float(lon)
            lat = float(lat)
            if ele == "0":
                ele = None
            else:
                ele = float(ele)
        t = None
        for ts in placemark.getElementsByTagName ("TimeStamp"):
            for e in ts.getElementsByTagName ("when"):
                t = dateutil.parser.parse (e.childNodes[0].data.strip())
        return Waypoint (lat, lon, ele, t, name)
