from telnetClient import *
import time

class TelnetMore:
    def __init__(self, ip, port, password, commandTimeout, socketTimeout):
        # Throws ValueError if unable to connect!
        # catch in code using this class

        self.telnetClient = TelnetClient(ip, port, password, socketTimeout)
        self.__commandTimeout = commandTimeout

    def __runAndOk(self, command, timeout):
        result = self.telnetClient.sendCommand(command, timeout)
        return result is not None and "OK" in result

    def startApp(self, packageName):
        return self.__runAndOk("more start %s\r\n" % (packageName), self.__commandTimeout)

    def stopApp(self, packageName):
        return self.__runAndOk("more stop %s\r\n" % (packageName), self.__commandTimeout)

    def restartApp(self, packageName):
        return self.__runAndOk("more restart %s\r\n" % (packageName), self.__commandTimeout)

    def resetAppdata(self, packageName):
        return self.__runAndOk("more reset %s\r\n" % (packageName), self.__commandTimeout)

    def clearAppCache(self, packageName):
        return self.__runAndOk("more cache %s\r\n" % (packageName), self.__commandTimeout)

    def turnScreenOn(self):
        return self.__runAndOk("more screen on\r\n", self.__commandTimeout)

    def click(self, x, y):
        return self.__runAndOk("screen click %s %s\r\n" % (str(x), str(y)), self.__commandTimeout)

    def getScreenshot(self, path):
        encoded = self.telnetClient.sendCommand("screen capture\r\n", self.__commandTimeout)
        if encoded is None:
            return False
        elif len(encoded) < 500 and "KO: " in encoded:
            log.error("getScreenshot: Could not retrieve screenshot. Check if mediaprojection is enabled!")
            return False
        fh = open(path, "wb")
        fh.write(encoded.decode('base64'))
        fh.close()
        return True

    def backButton(self):
        return self.__runAndOk("screen back\r\n", self.__commandTimeout)

    def isScreenOn(self):
        state = self.telnetClient.sendCommand("more state screen\r\n", self.__commandTimeout)
        if state is None:
            return False
        return "on" in state

    def isPogoTopmost(self):
        topmost = self.telnetClient.sendCommand("more topmost app\r\n", self.__commandTimeout)
        if topmost is None:
            return False
        return "com.nianticlabs.pokemongo" in topmost
