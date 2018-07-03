from vnc import connect

class VncWrapper:
    def __init__(self, ip, screen, port, password):
        self.ip = ip
        self.screen = screen #Default: 1
        self.port = port
        self.password = password


    def __getServerString(self):
        return str(self.ip) + ':' + str(self.screen) + ':' + str(self.port)

    def getScreenshot(self, path):
        client = connect(self.__getServerString(), self.password, timeout = 10)
        client.captureScreen(path) #TODO: consider passing path
        client.disconnect()

    def clickVnc(self, x, y):
        client = connect(self.__getServerString(), self.password, timeout = 10)
        client.mouseMove(x, y)
        client.mousePress(1)
        client.disconnect()

    def rightClickVnc(self):
        client = connect(self.__getServerString(), self.password, timeout = 10)
        client.mousePress(3)
        client.disconnect()
