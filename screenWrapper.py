from vnc.vncWrapper import VncWrapper
import logging

log = logging.getLogger(__name__)

class ScreenWrapper:
    def __init__(self, method, telnMore, vncIp, vncPort, vncPassword, vncScreen):
        self.method = method

        #don't create a self.screenWrapper for a combination of rgc and VNC at some point (depending on what's faster...)
        if method == 0:
            #stay in telnMore only mode
            self.telnMore = telnMore
            return
        else:
            #go for VNC. TODO: extend with combination of VNC and RGC
            print(str(vncIp), vncScreen, vncPort, vncPassword)
            self.vncWrapper = VncWrapper(str(vncIp), vncScreen, vncPort, vncPassword)

    def getScreenshot(self, path):
        if self.method == 0:
            log.debug("Trying to retrieve screenshot via RGC")
            return self.telnMore.getScreenshot(path)
        else:
            return self.vncWrapper.getScreenshot(path)

    def click(self, x, y):
        if self.method == 0:
            self.telnMore.click(x, y)
        else:
            self.vncWrapper.clickVnc(x, y)

    def backButton(self):
        if self.method == 0:
            self.telnMore.backButton()
        else:
            self.vncWrapper.rightClickVnc()
