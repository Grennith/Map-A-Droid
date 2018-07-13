from telnetClient import *

class TelnetMore:
    def __init__(self, ip, port, password):
        #Throws ValueError if unable to connect!
        #catch in code using this class
        self.telnetClient = TelnetClient(ip, port, password)

    def startApp(self, packageName):
        return self.telnetClient.sendCommand("more start %s\r\n" % (packageName))

    def stopApp(self, packageName):
        return self.telnetClient.sendCommand("more stop %s\r\n" % (packageName))

    def restartApp(self, packageName):
        return self.telnetClient.sendCommand("more restart %s\r\n" % (packageName))

    def resetAppdata(self, packageName):
        return self.telnetClient.sendCommand("more reset %s\r\n" % (packageName))

    def turnScreenOn(self):
        return self.telnetClient.sendCommand("more screen on\r\n")
