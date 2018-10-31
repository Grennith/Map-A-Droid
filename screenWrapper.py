import logging

log = logging.getLogger(__name__)

class ScreenWrapper:
    def __init__(self, websocketMore):
        self.websocketMore = websocketMore


    def getScreenshot(self, path):
        return self.websocketMore.getScreenshot(path)

    def click(self, x, y):
        self.websocketMore.click(x, y)

    def backButton(self):
        self.websocketMore.backButton()
