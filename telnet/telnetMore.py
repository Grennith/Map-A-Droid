from telnetClient import *

class TelnetMore:
    def __init__(self, ip, port, password):
        #Throws ValueError if unable to connect!
        #catch in code using this class

        self.telnetClient = TelnetClient(ip, port, password)

    def startApp(self, packageName):
        return self.telnetClient.sendCommand("more start %s\r\n" % (packageName))[0]

    def stopApp(self, packageName):
        return self.telnetClient.sendCommand("more stop %s\r\n" % (packageName))[0]

    def restartApp(self, packageName):
        return self.telnetClient.sendCommand("more restart %s\r\n" % (packageName))[0]

    def resetAppdata(self, packageName):
        return self.telnetClient.sendCommand("more reset %s\r\n" % (packageName))[0]

    def turnScreenOn(self):
        return self.telnetClient.sendCommand("more screen on\r\n")[0]

    def click(self, x, y):
        return self.telnetClient.sendCommand("screen click %s %s\r\n" % (str(x), str(y)))[0]

    def getScreenshot(self, path):
        return self.telnetClient.getScreenshot(path)

    def backButton(self):
        return self.telnetClient.sendCommand("screen back\r\n")[0]

    def isScreenOn(self):
        state = self.telnetClient.sendCommand("more state screen\r\n")[0]
        return "on" in state

    def isPogoTopmost(self):
        topmost = self.telnetClient.sendCommand("more topmost app\r\n")[0]
        return "com.nianticlabs.pokemongo" in topmost
