from fractions import gcd
import collections
import json
import logging
log = logging.getLogger(__name__)

AspectRatio = collections.namedtuple('AspectRatio', ['width', 'height'])
Coordinate = collections.namedtuple("Coordinate", ['x', 'y'])

#reference: 720x1280 (redmi 5a, 16:9)
referenceRatio = AspectRatio(16, 9)
referenceWidth = 720.0
referenceHeight = 1280.0
referencePpi = 296.0

#resolutions = {} #TODO: fill with config file
#reference positions of OK button, close, nearby stuff etc
referencePositions = {}

class ResolutionCalc:
    #TODO: consider loading config file
    def __init__(self, width, height):
        self.widht = width
        self.height = height
        with open('resolutions.json') as f:
            self.resolutions = json.load(f)
            log.info("resolutions.json loaded")
        #self.ppi = ppi
        commonDiv = gcd(width, height)
        self.aspectRatio = AspectRatio(width / commonDiv, height / commonDiv)
        self.aspectRatioString = str(self.aspectRatio.width) + ':' + str(self.aspectRatio.height)
        log.info("Calculated an aspect ratio of %s" % self.aspectRatioString)
        self.resolutionConfiguration = self.resolutions[self.aspectRatioString]
#check if windows/buttons stick to the bottom -> correct towards bottom (see 9:16 to 10:16 conversion)

    #get the correction factor of the x axis for a given reference X
    def __getXFactor(self, xRefPos):
        return referenceWidth / xRefPos #TODO: use referencePositions-dict

    def __getYFactor(self, yRefPos):
        return referenceHeight / yRefPos

    #the following methods are based on our reference device (Redmi 5A)
    def __getWidthMiddle(self):
        return self.width / 2.0

    def __getHeightMiddle(self):
        return self.height / 2.0

    #OK button's middle is at y = 98px below the middle of the screen on 296ppi
    def getLoginOkButton(self):
        x = self.__getWidthMiddle()
        #old concept for generic height
        #y = self.__getHeightMiddle() + 98.9 * (self.ppi / referencePpi)
        y = self.height * self.resolutionConfiguration['ok']['y']
        return Coordinate(x, y)

    def getNearby(self):
        x = self.width * self.resolutionConfiguration['nearby'][x]
        y = self.height * self.resolutionConfiguration['nearby'][y]
        return Coordinate(x, y)

    def getMenuClose(self):
        x = self.width * self.resolutionConfiguration['menu_close'][x]
        y = self.height * self.resolutionConfiguration['menu_close'][y]
        return Coordinate(x, y)

    def getQuestClose(self):
        x = self.width * self.resolutionConfiguration['quest_close'][x]
        y = self.height * self.resolutionConfiguration['quest_close'][y]
        return Coordinate(x, y)

    def getNearbyRaid(self):
        x = self.width * self.resolutionConfiguration['nearby_raid'][x]
        y = self.height * self.resolutionConfiguration['nearby_raid'][y]
        return Coordinate(x, y)

    def getNewsClose(self):
        x = self.width * self.resolutionConfiguration['news_close'][x]
        y = self.height * self.resolutionConfiguration['news_close'][y]
        return Coordinate(x, y)
