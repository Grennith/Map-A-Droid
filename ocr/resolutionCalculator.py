from fractions import gcd
import collections
import json
import logging
log = logging.getLogger(__name__)

AspectRatio = collections.namedtuple('AspectRatio', ['width', 'height'])
Coordinate = collections.namedtuple("Coordinate", ['x', 'y'])
Bounds = collections.namedtuple("Bounds", ['top', 'bottom', 'left', 'right'])

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
        self.width = width
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

    def __getBounds(self, id):
        left = self.width * self.resolutionConfiguration[id]['bounds']['left']
        right = self.width * self.resolutionConfiguration[id]['bounds']['right']
        top = self.height * self.resolutionConfiguration[id]['bounds']['top']
        bottom = self.height * self.resolutionConfiguration[id]['bounds']['bottom']
        left = int(round(left))
        right = int(round(right))
        top = int(round(top))
        bottom = int(round(bottom))
        return Bounds(top, bottom, left, right)

    def __getClick(self, id):
        x = self.width * self.resolutionConfiguration[id]['click']['x']
        y = self.height * self.resolutionConfiguration[id]['click']['y']
        x = int(round(x))
        y = int(round(y))
        return Coordinate(x, y)

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

    def getHeight(self):
        return height

    def getWidth(self):
        return width

    def getFirstHorizontalPxPosition(self):
        return int(round(self.resolutionConfiguration['crop']['lines']['firstCheckHorizontal'] * self.height))

    def getSecondHorizontalPxPosition(self):
        return int(round(self.resolutionConfiguration['crop']['lines']['secondCheckHorizontal'] * self.height))

    def getPostLoginOkDrivingBounds(self):
        return self.__getBounds('post_login_ok_driving')

    def getPostLoginOkPrivatePropertyBounds(self):
        return self.__getBounds('post_login_ok_private_property')

    #OK button's middle is at y = 98px below the middle of the screen on 296ppi
    def getPostLoginOkDrivingClick(self):
        #old concept for generic height
        #y = self.__getHeightMiddle() + 98.9 * (self.ppi / referencePpi)
        return self.__getClick('post_login_ok_driving')

    def getPostLoginOkPrivatePropertyClick(self):
        #old concept for generic height
        #y = self.__getHeightMiddle() + 98.9 * (self.ppi / referencePpi)
        return self.__getClick('post_login_ok_private_property')

    def getPostLoginNewsMessageBounds(self):
        return self.__getBounds('postLoginNewsMessage')

    def getSpeedwarningBounds(self):
        return self.__getBounds('speedwarning')

    def getSpeedwarningClick(self):
        return self.__getClick('speedwarning')

    def getNearbyClick(self):
        return self.__getClick('nearby')

    def getWeatherWarningFirstClick(self):
        return self.__getClick('weather_warning')

    def getWeatherWarningSecondClick(self):
        return self.__getClick('weather_window')

    def getWeatherWarningBounds(self):
        return self.__getBounds('weather_warning')

    def getNearbyRaidTabBounds(self):
        return self.__getBounds('nearby_raid_tab')

    def getNearbyRaidTabClick(self):
        return self.__getClick('nearby_raid_tab')

    def getQuitGamePopupBounds(self):
        return self.__getBounds('quit_game_popup')

    def getNewsQuestCloseButtonBounds(self):
        return self.__getBounds('news_or_quest_close')

    def getMenuRaidsCloseButtonBounds(self):
        return self.__getBounds('menu_or_raids_close')

    def getRaidcountBounds(self):
        return self.__getBounds('raidcount')

    def getRaidBounds(self, numberOfRaid):
        #numberOfRaid is 1 to 6
        if numberOfRaid < 1 or numberOfRaid > 6:
            return None
        #shift numberOfRaid to have index
        numberOfRaid -= 1
        lines = self.resolutionConfiguration['crop']['lines']['3+']
        column = numberOfRaid % 3 #columns 0 to 2
        row = 0
        if numberOfRaid > 2: #we are in the 2nd row...
            row = 1

        top = None
        bottom = None
        left = None
        right = None
        #arrays in resolutions would be better, but for readability's sake we
        #will use dicts/strings
        if row == 0:
            top = lines['horizontal']['first']
            bottom = lines['horizontal']['second']
        else:
            top = lines['horizontal']['second']
            bottom = lines['horizontal']['third']

        if column == 0:
            left = lines['vertical']['first']
            right = lines['vertical']['second']
        elif column == 1:
            left = lines['vertical']['second']
            right = lines['vertical']['third']
        else:
            left = lines['vertical']['third']
            right = lines['vertical']['fourth']

        left = int(round(left * self.width))
        right = int(round(right * self.width))
        top = int(round(top * self.height))
        bottom = int(round(bottom * self.height))
        return Bounds(top, bottom, left, right)

    def getRaidBoundsSingle(self):
        lines = self.resolutionConfiguration['crop']['lines']['1']
        top = lines['horizontal']['first']
        bottom = lines['horizontal']['second']
        left = lines['vertical']['first']
        right = lines['vertical']['second']

        left = int(round(left * self.width))
        right = int(round(right * self.width))
        top = int(round(top * self.height))
        bottom = int(round(bottom * self.height))
        return Bounds(top, bottom, left, right)

    def getRaidBoundsTwo(self, numberOfRaid):
        lines = self.resolutionConfiguration['crop']['lines']['2']
        top = None
        bottom = None
        left = None
        right = None
        top = lines['horizontal']['first']
        bottom = lines['horizontal']['second']

        if numberOfRaid == 1:
            left = lines['vertical']['first']
            right = lines['vertical']['second']
        else:
            left = lines['vertical']['second']
            right = lines['vertical']['third']

        left = int(round(left * self.width))
        right = int(round(right * self.width))
        top = int(round(top * self.height))
        bottom = int(round(bottom * self.height))
        return Bounds(top, bottom, left, right)
