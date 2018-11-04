import sys
import socket
import select
import time
import logging

log = logging.getLogger()

class WebsocketMore:
    def __init__(self, websocketServer, commandTimeout, screenshotIp, screenshotPort, screenshotTimeout):
        # Throws ValueError if unable to connect!
        # catch in code using this class

        self.websocketServer = websocketServer
        self.__commandTimeout = commandTimeout
        self.__ip = screenshotIp
        self.__port = screenshotPort
        self.__socketTimeout = screenshotTimeout
        self.__commandTimeout = commandTimeout

    def __runAndOk(self, command, timeout):
        result = self.websocketServer.sendCommand(command, timeout)
        return result is not None and "OK" in result

    def startApp(self, packageName):
        return self.__runAndOk("more start %s\r\n" % (packageName), self.__commandTimeout)

    def stopApp(self, packageName):
        if not self.__runAndOk("more stop %s\r\n" % (packageName), self.__commandTimeout):
            log.error("Failed stopping %s, please check if SU has been granted" % packageName)
            return False
        else:
            return True

    def restartApp(self, packageName):
        return self.__runAndOk("more restart %s\r\n" % (packageName), self.__commandTimeout)

    def resetAppdata(self, packageName):
        return self.__runAndOk("more reset %s\r\n" % (packageName), self.__commandTimeout)

    def clearAppCache(self, packageName):
        return self.__runAndOk("more cache %s\r\n" % (packageName), self.__commandTimeout)

    def turnScreenOn(self):
        return self.__runAndOk("more screen on\r\n", self.__commandTimeout)

    def click(self, x, y):
        return self.__runAndOk("screen click %s %s\r\n" % (str(int(round(x))), str(int(round(y)))), self.__commandTimeout)

    def __close_socket(self, connection):
        try:
            connection.shutdown(socket.SHUT_RDWR)
        except:
            pass
        try:
            connection.close()
        except:
            pass

    def __read(self, s):
        """Read data and return the read bytes."""
        try:
            ready = select.select([s], [], [], self.__commandTimeout)
        except select.error as err:
            log.error("__read: Timeout retrieving message: %s" % str(err))
            self.__close_socket(s)
            return b''
        try:
            data = s.recv(4096)
            return data
        except (socket.timeout, AttributeError, OSError):
            log.warning("Sockettimeout, Attribute or OSError")
            self.__close_socket(s)
            return b''
        except: #attribute, conn reset etc etc
            log.warning("Other error trying to receive data")
            self.__close_socket(s)
            return b''

    def __connectImageSocket(self, s):
        try:
            log.debug("Retrieving screenshot from: %s:%s" % (str(self.__ip), str(self.__port)))
            s.connect((self.__ip, self.__port))
            s.setblocking(1)
            s.settimeout(self.__socketTimeout)
            return True
        except:
            log.warning("telnetMore::getScreenshot: Failed connecting to socket...")
            return False

    def getScreenshot(self, path):
        encoded = self.websocketServer.sendCommand("screen capture\r\n", self.__commandTimeout)
        if encoded is None:
            return False
        elif len(encoded) < 500 and "KO: " in encoded:
            log.error("getScreenshot: Could not retrieve screenshot. Check if mediaprojection is enabled!")
            return False
        elif not "OK:" in encoded:
            log.error("getScreenshot: response not OK")
            return False
        elif not "size:" in encoded:
            log.error("getScreenshot: won't be able to read a size, aborting")
            return False
        # extract the length of the image from encoded
        # first split by ',', then by ':'
        keyVals = encoded.split(',')
        size = 0
        for key in keyVals:
            if "size:" in key:
                size = int(key.split(':')[1])
                break
        if size == 0:
            log.error("getScreenshot: invalid size")
            return False

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        attempts = 0
        while not self.__connectImageSocket(s):
            attempts = attempts + 1
            time.sleep(0.5)
            if attempts > 100:
                log.error("Could not connect to the image socket in 100 attempts")
                self.__close_socket(s)
                return False
            
        sizeToReceive = size
        image = self.__read(s)
        while sizeToReceive >= sys.getsizeof(image):
            received = self.__read(s)
            if received == b'':
                log.warning("Received empty line")
                return False
            image = image + received

        self.__close_socket(s)
        fh = open(path, "wb")
        fh.write(image)
        fh.close()
        return True

    def backButton(self):
        return self.__runAndOk("screen back\r\n", self.__commandTimeout)

    def isScreenOn(self):
        state = self.websocketServer.sendCommand("more state screen\r\n", self.__commandTimeout)
        if state is None:
            return False
        return "on" in state

    def isPogoTopmost(self):
        topmost = self.websocketServer.sendCommand("more topmost app\r\n", self.__commandTimeout)
        if topmost is None:
            return False
        return "com.nianticlabs.pokemongo" in topmost
