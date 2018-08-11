from telnetClient import *
import time

class TelnetMore:
    def __init__(self, ip, port, password):
        #Throws ValueError if unable to connect!
        #catch in code using this class

        self.telnetClient = TelnetClient(ip, port, password)

    def startApp(self, packageName):
        return self.telnetClient.sendCommand("more start %s\r\n" % (packageName), 10)

    def stopApp(self, packageName):
        return self.telnetClient.sendCommand("more stop %s\r\n" % (packageName), 10)

    def restartApp(self, packageName):
        return self.telnetClient.sendCommand("more restart %s\r\n" % (packageName), 10)

    def resetAppdata(self, packageName):
        return self.telnetClient.sendCommand("more reset %s\r\n" % (packageName), 10)

    def clearAppCache(self, packageName):
        return self.telnetClient.sendCommand("more cache %s\r\n" % (packageName), 10)

    def turnScreenOn(self):
        return self.telnetClient.sendCommand("more screen on\r\n", 10)

    def click(self, x, y):
        return self.telnetClient.sendCommand("screen click %s %s\r\n" % (str(x), str(y)), 10)

    def getScreenshot(self, path):
        encoded = self.telnetClient.sendCommand("screen capture\r\n", 10)
        if encoded is None:
            return False
        fh = open(path, "wb")
        fh.write(encoded.decode('base64'))
        fh.close()
        return True

    def backButton(self):
        return self.telnetClient.sendCommand("screen back\r\n", 10)[0]

    def isScreenOn(self):
        state = self.telnetClient.sendCommand("more state screen\r\n", 10)
        if state is None:
            return False
        return "on" in state

    def isPogoTopmost(self):
        topmost = self.telnetClient.sendCommand("more topmost app\r\n", 15)
        if topmost is None:
            return False
        return "com.nianticlabs.pokemongo" in topmost
