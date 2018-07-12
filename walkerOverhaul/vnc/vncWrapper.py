from vnc import connect, TimeoutError

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
        success = True
        try:
            client.captureScreen(path)
        except (TimeoutError):
            success = False
        finally:
            client.disconnect()
        return success

    def clickVnc(self, x, y):
        client = connect(self.__getServerString(), self.password, timeout = 10)
        success = True
        try:
            client.mouseMove(x, y)
            client.mousePress(1)
        except (TimeoutError):
            success = False
        finally:
            client.disconnect()
        return success

    def rightClickVnc(self):
        client = connect(self.__getServerString(), self.password, timeout = 10)
        success = True
        try:
            client.mousePress(3)
        except (TimeoutError):
            success = False
        finally:
            client.disconnect()
        return success
