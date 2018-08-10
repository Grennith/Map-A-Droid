import socket
import select
import time
import logging
import sys

log = logging.getLogger()


class TelnetClient:
    def __init__(self, ip, port, password):
        self.passwordSet = (password is not None and len(password) > 0)
        if self.passwordSet:
            log.debug('Trying to build up a telnet connection to %s:%s with a password'
                % (str(ip), str(port)))
        else:
            log.debug('Trying to build up a telnet connection to %s:%s without a password'
                % (str(ip), str(port)))

        self.__ip = ip
        self.__port = port
        self.__password = password
        self.__sock = None
        self.connected = None  # keep those two values for later use...
        self.authenticated = None
        self.__setupSocket()

    def __del__(self):
        self.__sock.close()

    def __connectSocket(self):
        try:
            self.__sock.connect((self.__ip, self.__port))
            self.__sock.settimeout(30)
            return True
        except socket.error as ex:
            return False

    # returns tuple (messageAvailable : bool, answer : string)
    def __retrieveMessage(self, timeout, again=False):
        result = None
        ready = None
        try:
            ready = select.select([self.__sock], [], [], timeout)
        except select.error as err:
            log.error("__retrieveMessage: Timeout retrieving message: %s" % str(err))
            self.__reconnect()
            return None

        if ready[0]:
            try:
                returnedLine = self.__sock.recv(4096)
                if len(returnedLine) <= 2:
                    # empty line...
                    log.warning("__retrieveMessage: Received empty line")
                    if again:
                        log.warning("__retrieveMessage: retrieved empty lines twice")
                        self.__reconnect()
                        return None
                    else:
                        return self.__retrieveMessage(4, again=True)
                returnedLineSplit = returnedLine.split('_', 1)
                count = int(returnedLineSplit[0])
                result = returnedLineSplit[1]
                while len(result) < count:
                    result += self.__sock.recv(4096)

                result = result.rstrip()
                log.debug("__retrieveMessage: Received message: %s" % result)
                return result
            except socket.error as e:
                log.error("__retrieveMessage: socket.error: %s" % str(e))
                # if e.errno != errno.ECONNRESET:
                # TODO: read errno
                log.error(str(e.errno))
                # try to reconnect
                self.__reconnect()
                return None
            except ValueError as e:
                log.error("__retrieveMessage: Failed reading the line length. Reconnecting...")
                self.__reconnect()
                return None
            except socket.timeout as e:
                log.error("__retrieveMessage: Timeout during socket.recv")
                self.__reconnect()
                return None
            except Exception as e:
                log.fatal("__retrieveMessage: Unexpected exception %s" % str(e))
                self.__reconnect()
                return None
        else:
            log.error("__retrieveMessage: Timeout retrieving message")
            self.__reconnect()
            return None

    def __sendCommand(self, command):
        totalsent = 0
        log.debug("__sendCommand: sending command '%s'" % command)
        while totalsent < len(command):
            sent = self.__sock.send(command[totalsent:])
            if sent == 0:
                # connection lost, reconnect...
                log.error("__sendCommand: Lost connection...")
                self.__reconnect()
                return False
                # raise RuntimeError("socket connection broken")
            totalsent = totalsent + sent
        return True

    def sendCommand(self, command, timeout):
        # any reconnects are handled within sendCommand and retrieveMessage!
        if not self.__sendCommand(command):
            # failed sending...
            log.error("sendCommand: Failed sending command")
            return None
        else:
            received = self.__retrieveMessage(timeout)
            if received is None:
                log.error("sendCommand: Got None (error or timeout)...")
                return None
            elif "KO: password required." in received:
                log.fatal("sendCommand: Missing authentication in telnet...")
                sys.exit(1)
            return received

    def __auth(self):
        if not self.passwordSet:
            log.debug("__auth: No password configured, not authenticating...")
            return True
        log.debug("__auth: Trying to authenticate")
        command = "auth %s\r\n" % str(self.__password)
        result = self.sendCommand(command, 3)
        if result is None:
            # experienced an error...
            log.error("__auth: Something went wrong while authenticating")
            return None
        elif "OK" in result:
            return True
        else:
            # wrong password or whatever...
            return False

    def __setupSocket(self):
        self.__sock = socket.socket()
        attempts = 0
        while not self.__connectSocket() and attempts < 10:
            time.sleep(1)
            attempts += 1
        if attempts >= 10:
            log.fatal("__setupSocket: Failed to connect to RGC. Shutting down.")
            sys.exit(1)

        self.connected = True
        lastMessage = ""
        while "OK" not in lastMessage:
            lastMessage = self.__retrieveMessage(3)
            if lastMessage is None:
                # experienced an error...
                self.connected = False
                return
        self.authenticated = self.__auth()

    def __reconnect(self):
        self.__sock.close()
        time.sleep(1)
        self.__setupSocket()
