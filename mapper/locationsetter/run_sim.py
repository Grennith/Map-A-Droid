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

INDEX = "/whereami/whereami.html"
UPDATE_INTERVAL = 0.3

curr_lat = 48.7833  # updated by main thread, read by http and geofix threads
curr_lon = 9.1833   # updated by main thread, read by http and geofix threads


def main(args):
    global curr_lon
    global curr_lat

    try:
        track = gpxdata.Track.fromGPX(gpxdata.parse(args.gpx_file))
    except Exception as ex:
        print("Error loading a track from the GPX file: %s" % ex)
        sys.exit(2)

    def create_track_iter():
        for segment in track:
            for point in segment:
                yield point
    track_iter = create_track_iter()
    try:
        point = next(track_iter)
    except StopIteration:
        print("No points found in the track. Exiting.")
        exit(1);
    curr_lon = point.lon
    curr_lat = point.lat

    if args.listen_ip:
        http_thread = threading.Thread(target=start_http_server, args=(args,))
        http_thread.daemon = True
        http_thread.start()
        time.sleep(1)

    geofix_thread = threading.Thread(target=start_geofix, args=(args,))
    geofix_thread.daemon = True
    geofix_thread.start()

    t_speed = None
    if args.speed:
        t_speed = args.speed / 3.6

    print("Location mocking started.")
    if not t_speed:
        walk_track_interval(track_iter, float(args.sleep), point)
    else:
        walk_track_speed(track_iter, t_speed, point)


def walk_track_interval(track, t_sleep, _):
    global curr_lon
    global curr_lat
    while True:
        time.sleep(t_sleep)
        try:
            point = next(track)
        except StopIteration:
            print("done")
            sys.exit(0)
        curr_lon = point.lon
        curr_lat = point.lat


def walk_track_speed(track, speed, point):
    global curr_lon
    global curr_lat
    while True:
        try:
            next_point = next(track)
        except StopIteration:
            print("done")
            sys.exit(0)
        distance = point.distance(next_point)
        travel_time = distance / speed  # in seconds

        if travel_time <= UPDATE_INTERVAL:
            time.sleep(travel_time)
        while travel_time > UPDATE_INTERVAL:
            time.sleep(UPDATE_INTERVAL)
            travel_time -= UPDATE_INTERVAL
            # move GEOFIX_UPDATE_INTERVAL*speed meters
            # in straight line between last_point and point
            course = point.course(next_point)
            distance = UPDATE_INTERVAL * speed
            point = point + gpxdata.CourseDistance(course, distance)
            curr_lat = point.lat
            curr_lon = point.lon

        point = next_point
        curr_lat = point.lat
        curr_lon = point.lon


def start_geofix(args):
    s = socket.socket()
    try:
        s.connect((args.ip, args.port))
    except socket.error as ex:
        print("Error connecting to %s:%s (%s)" % (args.ip, args.port, ex))
        thread.interrupt_main()

    try:
        while True:
            rlist, wlist, _ = select.select([s], [s], [])
            if s in rlist:
                x = s.recv(1024)
                if "KO: password required" in x:
                    s.close()
                    print("Password protection is enabled MockGeoFix settings. This is not supported.")
                    sys.exit(2)
                if x == '':
                    s.close()
                    print("Connection closed.")
                    thread.interrupt_main()
            if s in wlist:
                s.send("geo fix %f %f\r\n" % (curr_lat, curr_lon))
            time.sleep(UPDATE_INTERVAL)
    except socket.error as ex:
        print(ex)
        thread.interrupt_main()


def start_http_server(args):
    import SimpleHTTPServer
    import SocketServer
    from StringIO import StringIO

    class Handler(SimpleHTTPServer.SimpleHTTPRequestHandler):
        def do_GET(self):
            if self.path.strip() == "/":
                self.send_response(301)
                self.send_header("Location", INDEX)
                self.end_headers()
                return None
            elif self.path.strip() == "/getpos":
                return self.get_position()
            return SimpleHTTPServer.SimpleHTTPRequestHandler.do_GET(self)

        def get_position(self):
            f = StringIO()
            f.write("""{
                "status": "OK",
                "accuracy": 10.0,
                "location": {"lat": %f, "lng": %f}
            }""" % (curr_lat, curr_lon))
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            length = f.tell()
            f.seek(0)
            self.send_header("Content-Length", str(length))
            self.end_headers()
            self.copyfile(f, self.wfile)

        def list_directory(self, _):
            self.path = "/"
            return self.do_GET()

        def log_message(self, *_):
            return

    class TCPServer(SocketServer.TCPServer):
        def server_bind(self):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind(self.server_address)

        def handle_error(self, request, client_address):
            if sys.exc_info()[0] == socket.error:
                return  # client probably closed connection
            return SocketServer.TCPServer.handle_error(self, request, client_address)

    try:
        httpd = TCPServer((args.listen_ip, args.listen_port), Handler)
    except Exception as ex:
        print("Error starting HTTP server: %s" % ex)
        thread.exit()

    print("Open http://%s:%s in your web browser." % (args.listen_ip, args.listen_port))
    httpd.serve_forever()

if __name__ == '__main__':
    args_parser = argparse.ArgumentParser()
    args_parser.add_argument("-i", "--ip", help="connect to MockGeoFix using this IP address",
                             required=True)
    args_parser.add_argument("-p", "--port", default=5554, help="default: 5554", type=int)
    args_parser.add_argument("-g", "--gpx-file", required=True)
    args_parser.add_argument("-S", "--sleep", help="sleep between track points (default: 0.5)",
                             required=False, default=0.5, type=float)
    args_parser.add_argument("-s", "--speed", help="speed in km/h (takes precedence over -S)",
                             required=False, type=float)
    args_parser.add_argument("-I", "--listen-ip",
                             help="Run a HTTP server visualizing mocked location on this ip.",
                             required=False)
    args_parser.add_argument("-P", "--listen-port", help="HTTP server's port (default: 80)",
                             required=False, default=80, type=int)

    args = args_parser.parse_args()

    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    try:
        main(args)
    except KeyboardInterrupt:
        print("Exiting.")
