import logging
import mysql
import mysql.connector
import datetime
import collections
import datetime
import time
from webhook import send_webhook
from walkerArgs import parseArgs
import requests
import shutil
import sys
import os

log = logging.getLogger(__name__)

RaidLocation = collections.namedtuple('RaidLocation', ['latitude', 'longitude'])
args = parseArgs()


class MonocleWrapper:
    def __init__(self, host, port, user, password, database, timezone, uniqueHash="123"):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.timezone = timezone
        self.uniqueHash = uniqueHash
        self.lastUpdatedPresent = self.__ensureLastUpdatedColumn()
        if self.lastUpdatedPresent:
            self.timestampColumn = 'last_updated'
        else:
            self.timestampColumn = 'time_spawn'

    def __checkLastUpdatedColumnExists(self):
        try:
            connection = mysql.connector.connect(host=self.host,
                                                 user=self.user, port=self.port, passwd=self.password,
                                                 db=self.database)
        except:
            log.error("Could not connect to the SQL database")
            return False

        query = "SELECT count(*) FROM information_schema.columns " \
                "WHERE table_name = 'raids' AND column_name = 'last_updated'"
        cursor = connection.cursor()
        cursor.execute(query)
        result = int(cursor.fetchall()[0][0])
        cursor.close()
        connection.close()
        return int(result)

    # TODO: consider adding columns for last_updated timestamp to not abuse time_spawn in raids
    def __ensureLastUpdatedColumn(self):
        log.info("Checking if last_updated column exists in raids table and creating it if necessary")

        result = self.__checkLastUpdatedColumnExists()
        if result == 1:
            log.info("raids.last_updated already present")
            return True

        try:
            connection = mysql.connector.connect(host=self.host,
                                                 user=self.user, port=self.port, passwd=self.password,
                                                 db=self.database)
        except:
            log.error("Could not connect to the SQL database")
            return False

        alterQuery = "ALTER TABLE raids ADD COLUMN last_updated int(11) NULL after time_end"
        cursor = connection.cursor()
        cursor.execute(alterQuery)
        connection.commit()

        if self.__checkLastUpdatedColumnExists() == 1:
            log.info("Successfully added last_updated column")
            return True
        else:
            log.warning("Could not add last_updated column, fallback to time_spawn")
            return False

    def dbTimeStringToUnixTimestamp(self, timestring):
        dt = datetime.datetime.strptime(timestring, '%Y-%m-%d %H:%M:%S.%f')
        unixtime = (dt - datetime.datetime(1970, 1, 1)).total_seconds()
        return unixtime

    def getNextRaidHatches(self, delayAfterHatch):
        try:
            connection = mysql.connector.connect(host=self.host,
                                                 user=self.user, port=self.port, passwd=self.password,
                                                 db=self.database)
        except:
            log.error("Could not connect to the SQL database")
            return []
        cursor = connection.cursor()

        # dbTimeToCheck = self.dbTimeStringToUnixTimestamp(
        #    str(datetime.datetime.now() - datetime.timedelta(hours=self.timezone)))
        dbTimeToCheck = time.time()
        query = (' SELECT time_battle, lat, lon FROM raids LEFT JOIN forts ' +
                 'ON raids.fort_id = forts.id WHERE raids.time_end > \'%s\' ' % str(dbTimeToCheck) +
                 'AND raids.pokemon_id IS NULL')
        # print(query)
        # data = (datetime.datetime.now())
        cursor.execute(query)

        data = []
        log.debug("Result of raidQ query: %s" % str(query))
        for (time_battle, lat, lon) in cursor:
            if lat is None or lon is None:
                log.warning("lat or lng is none")
                continue
            # timestamp = self.dbTimeStringToUnixTimestamp(str(start))
            data.append((time_battle + delayAfterHatch * 60, RaidLocation(lat, lon)))

        log.debug("Latest Q: %s" % str(data))
        connection.commit()
        return data

    def createHashDatabaseIfNotExists(self):
        log.debug('Creating hash db in database')
        try:
            connection = mysql.connector.connect(host=self.host,
                                                 user=self.user, port=self.port, passwd=self.password,
                                                 db=self.database)
        except:
            log.error("Could not connect to the SQL database")
            return False
        cursor = connection.cursor()
        query = (' Create table if not exists trshash ( ' +
                 ' hashid MEDIUMINT NOT NULL AUTO_INCREMENT, ' +
                 ' hash VARCHAR(255) NOT NULL, ' +
                 ' type VARCHAR(10) NOT NULL, ' +
                 ' id VARCHAR(255) NOT NULL, ' +
                 ' count INT(10) NOT NULL DEFAULT 1, ' +
                 ' PRIMARY KEY (hashid))')
        log.debug(query)
        cursor.execute(query)
        connection.commit()
        return True

    def checkForHash(self, imghash, type, raidNo):
        log.debug(
            '[Crop: ' + str(raidNo) + ' (' + str(self.uniqueHash) + ') ] ' + 'checkForHash: Checking for hash in db')
        try:
            connection = mysql.connector.connect(host=self.host,
                                                 user=self.user, port=self.port, passwd=self.password,
                                                 db=self.database)
        except:
            log.error("Could not connect to the SQL database")
            return None
        cursor = connection.cursor()

        query = (' SELECT  id, BIT_COUNT( ' +
                 ' CONV(hash, 16, 10) ^ CONV(\'' + str(imghash) + '\', 16, 10) ' +
                 ' ) as hamming_distance, type ' +
                 ' FROM trshash ' +
                 ' HAVING hamming_distance < 4 and type = \'' + str(type) + '\'' +
                 ' ORDER BY hamming_distance ASC')

        cursor.execute(query)
        id = None
        data = cursor.fetchall()
        number_of_rows = cursor.rowcount
        log.debug('[Crop: ' + str(raidNo) + ' (' + str(
            self.uniqueHash) + ') ] ' + 'checkForHash: Found Hashes in Database: %s' % str(number_of_rows))
        if number_of_rows > 0:
            log.debug(
                '[Crop: ' + str(raidNo) + ' (' + str(self.uniqueHash) + ') ] ' + 'checkForHash: Returning found ID')
            for row in data:
                log.debug(
                    '[Crop: ' + str(raidNo) + ' (' + str(self.uniqueHash) + ') ] ' + 'checkForHash: ID: ' + str(row[0]))
                return True, row[0]
        else:
            log.debug(
                '[Crop: ' + str(raidNo) + ' (' + str(self.uniqueHash) + ') ] ' + 'checkForHash: No matching Hash found')
            return False, None

    def insertHash(self, imghash, type, id, raidNo):
        doubleCheck = self.checkForHash(imghash, type, raidNo)
        if doubleCheck[0]:
            log.debug('[Crop: ' + str(raidNo) + ' (' + str(
                self.uniqueHash) + ') ] ' + 'insertHash: Already in DB - update Counter')
        try:
            connection = mysql.connector.connect(host=self.host,
                                                 user=self.user, port=self.port, passwd=self.password,
                                                 db=self.database)
        except:
            log.error("Could not connect to the SQL database")
            return False
        cursor = connection.cursor()
        if not doubleCheck[0]:
            query = (' INSERT INTO trshash ' +
                     ' ( hash, type, id ) VALUES ' +
                     ' (\'%s\', \'%s\', \'%s\')'
                     % (str(imghash), str(type), str(id)))
        else:
            query = (' UPDATE trshash ' +
                     ' set count=count+1 '
                     ' where hash=\'%s\''
                     % (str(imghash)))

        cursor.execute(query)
        connection.commit()
        return True

    def deleteHashTable(self, ids, type):
        log.debug('Deleting old Hashes of type %s' % type)
        log.debug('Valid ids: %s' % ids)
        try:
            connection = mysql.connector.connect(host=self.host,
                                                 user=self.user, port=self.port, passwd=self.password,
                                                 db=self.database)
        except:
            log.error("Could not connect to the SQL database")
            return False
        cursor = connection.cursor()
        query = (' DELETE FROM trshash ' +
                 ' where id not in (' + ids + ') ' +
                 ' and type like \'%' + type + '%\'')
        log.debug(query)
        cursor.execute(query)
        connection.commit()
        return True

    # apparently external_id in raids won't always match the one in forts. Great....
    def __getFortIdWithExternalId(self, externalId):
        try:
            connection = mysql.connector.connect(host=self.host,
                                                 user=self.user, port=self.port, passwd=self.password,
                                                 db=self.database)
        except:
            log.error("Could not connect to the SQL database")
            return False

        log.error("__getFortIdWithExternalId: Trying to retrieve ID of '%s'" % str(externalId))
        query = "SELECT id FROM `forts` WHERE external_id='%s'" % str(externalId)
        cursor = connection.cursor()
        log.debug("__getFortIdWithExternalId: Executing query: %s " % str(query))

        cursor.execute(query)
        idList = cursor.fetchall()
        if len(idList) == 0:
            log.error("__getFortIdWithExternalId: Gym does not exist in DB")
            return None
        elif len(idList) > 1:
            log.warning("__getFortIdWithExternalId: Multiple gyms with the same external ID...")

        idEntry = idList[0]
        log.error(str(idEntry[0]))
        return idEntry[0]

    def submitRaid(self, gym, pkm, lvl, start, end, type, raidNo, captureTime, MonWithNoEgg=False):
        log.debug('[Crop: ' + str(raidNo) + ' (' + str(self.uniqueHash) + ') ] ' + 'submitRaid: Submitting raid')
        zero = datetime.datetime.now()
        zero = time.mktime(zero.timetuple())  # - (self.timezone * 60 * 60)

        #if end is None and not MonWithNoEgg:
        #    # nothing to be done except for refreshing scantimes
        #    log.info('[Crop: ' + str(raidNo) + ' (' + str(self.uniqueHash) + ') ] ' +
        #             'submitRaid: Raid on gym ' + str(gym) + ' previously reported, nothing changed. '
         #                                                    'Just gonna update last_scanned')
        #    self.refreshTimes(gym, type, raidNo)
        #    return False
        # if self.raidExist(gym, type, raidNo):
        #    self.refreshTimes(gym, raidNo, captureTime)
        #    log.debug('[Crop: ' + str(raidNo) + ' (' + str(
        #        self.uniqueHash) + ') ] ' + 'submitRaid: %s already submitted - ignoring' % str(type))
        #    return False

        try:
            connection = mysql.connector.connect(host=self.host,
                                                 user=self.user, port=self.port, passwd=self.password,
                                                 db=self.database)
        except:
            log.error("Could not connect to the SQL database")
            return False

        wh_send = False
        eggHatched = False
        cursor = connection.cursor()
        log.debug('[Crop: ' + str(raidNo) + ' (' + str(
            self.uniqueHash) + ') ] ' + 'submitRaid: Submitting something of type %s' % type)

        log.info("Submitting. Gym: %s, Lv: %s, Start and Spawn: %s, End: %s, Mon: %s" % (gym, lvl, start, end, pkm))

        # always insert timestamp to time_spawn to have rows change if raid has been reported before
        updateStr = 'UPDATE raids '
        whereStr = 'WHERE fort_id = %s AND time_end >= %s' % (str(gym), str(int(time.time())))
        if MonWithNoEgg:
            # submit mon without egg info -> we have an endtime
            start = end - 45 * 60
            log.info("Updating mon without egg")

            if self.lastUpdatedPresent:
                setStr = 'SET level = %s, time_spawn = %s, time_battle = %s, time_end = %s, ' \
                         'pokemon_id = %s, ' + self.timestampColumn + ' = %s '
                data = (lvl, captureTime, start, end, pkm, int(time.time()))
            else:
                setStr = 'SET level= %s, time_spawn = %s, time_battle = %s, time_end = %s, pokemon_id = %s '
                data = (lvl, int(time.time()), start, end, pkm)

        elif end is None or start is None:
            # no end or start time given, just update the other stuff
            # TODO: consider skipping UPDATING/INSERTING
            # TODO: this will be an update of a hatched egg to a boss!
            log.info("Updating without endtime or starttime - we should've seen an egg before then")
            setStr = 'SET level = %s, pokemon_id = %s, ' + self.timestampColumn + ' = %s '
            data = (lvl, pkm, int(time.time()))

            foundEndTime, EndTime = self.getRaidEndtime(gym, raidNo)

            if foundEndTime:
                wh_send = True
                wh_start = int(EndTime) - 2700
                wh_end = EndTime
                eggHatched = True
            else:
                wh_send = False

            # TODO: check for start/end
        else:
            log.info("Updating everything")
            # we have start and end, mon is either with egg or we're submitting an egg
            if self.lastUpdatedPresent:
                setStr = 'SET level = %s, time_spawn = %s, time_battle = %s, time_end = %s, pokemon_id = %s, ' \
                         'last_updated = %s '
                data = (lvl, captureTime, start, end, pkm, int(time.time()))
            else:
                setStr = 'SET level = %s, time_spawn = %s, time_battle = %s, time_end = %s, pokemon_id = %s, ' \
                         'last_updated = %s '
                data = (lvl, int(time.time()), start, end, pkm)

        query = updateStr + setStr + whereStr
        log.debug(query % data)
        cursor.execute(query, data)
        affectedRows = cursor.rowcount
        connection.commit()
        cursor.close()
        if affectedRows == 0 and not eggHatched:
            # we need to insert the raid...
            log.info("Gotta insert")
            if MonWithNoEgg:
                # submit mon without egg info -> we have an endtime
                log.info("Inserting mon without egg")
                start = end - 45 * 60
                query = (
                    'INSERT INTO raids (fort_id, level, time_spawn, time_battle, time_end, pokemon_id) '
                    'VALUES (%s, %s, %s, %s, %s, %s)')
                data = (gym, lvl, captureTime, start, end, pkm)
            elif end is None or start is None:
                log.info("Inserting without end or start")
                # no end or start time given, just inserting won't help much...
                log.warning("Useless to insert without endtime...")
                return False
            else:
                # we have start and end, mon is either with egg or we're submitting an egg
                log.info("Inserting everything")
                query = (
                    'INSERT INTO raids (fort_id, level, time_spawn, time_battle, time_end, pokemon_id) '
                    'VALUES (%s, %s, %s, %s, %s, %s)')
                data = (gym, lvl, captureTime, start, end, pkm)

            cursorIns = connection.cursor()
            log.debug(query % data)
            cursorIns.execute(query, data)
            connection.commit()
            cursorIns.close()

            wh_send = True
            if MonWithNoEgg:
                wh_start = int(end) - 2700
            else:
                wh_start = start
            wh_end = end
            if pkm is None:
                pkm = 0

        log.info('[Crop: ' + str(raidNo) + ' (' + str(self.uniqueHash) + ') ] ' + 'submitRaid: Submit finished')
        self.refreshTimes(gym, raidNo, captureTime)

        if args.webhook and wh_send:
            log.info('[Crop: ' + str(raidNo) + ' (' + str(self.uniqueHash) + ') ] ' + 'submitRaid: Send webhook')
            send_webhook(gym, 'RAID', wh_start, wh_end, lvl, pkm)

        return True

    def readRaidEndtime(self, gym, raidNo):
        log.debug('[Crop: ' + str(raidNo) + ' (' + str(
            self.uniqueHash) + ') ] ' + 'readRaidEndtime: Check DB for existing mon')
        # now = self.dbTimeStringToUnixTimestamp(str(datetime.datetime.now() - datetime.timedelta(hours=self.timezone)))
        now = time.time()
        try:
            connection = mysql.connector.connect(host=self.host,
                                                 user=self.user, port=self.port, passwd=self.password,
                                                 db=self.database)
        except:
            log.error("Could not connect to the SQL database")
            return False

        cursor = connection.cursor()
        query = (' SELECT time_end FROM raids ' +
                 ' WHERE time_end >= ' + str(now) + ' and fort_id = \'' + str(gym) + '\'')
        cursor.execute(query)
        data = cursor.fetchall()
        number_of_rows = cursor.rowcount
        if number_of_rows > 0:
            for row in data:
                log.debug('[Crop: ' + str(raidNo) + ' (' + str(
                    self.uniqueHash) + ') ] ' + 'readRaidEndtime: Found Rows: %s' % str(number_of_rows))
                log.info('[Crop: ' + str(raidNo) + ' (' + str(
                    self.uniqueHash) + ') ] ' + 'readRaidEndtime: Endtime already submitted')
                return True

        log.info('[Crop: ' + str(raidNo) + ' (' + str(
            self.uniqueHash) + ') ] ' + 'readRaidEndtime: Endtime is new - submitting')
        return False

    def getRaidEndtime(self, gym, raidNo):
        log.debug('[Crop: ' + str(raidNo) + ' (' + str(
            self.uniqueHash) + ') ] ' + 'getRaidEndtime: Check DB for existing mon')
        # now = self.dbTimeStringToUnixTimestamp(str(datetime.datetime.now() - datetime.timedelta(hours=self.timezone)))
        now = time.time()
        try:
            connection = mysql.connector.connect(host=self.host,
                                                 user=self.user, port=self.port, passwd=self.password,
                                                 db=self.database)
        except:
            log.error("Could not connect to the SQL database")
            return False

        cursor = connection.cursor()
        query = (' SELECT time_end FROM raids ' +
                 ' WHERE time_end >= ' + str(now) + ' and fort_id = \'' + str(gym) + '\'')

        cursor.execute(query)
        data = cursor.fetchall()
        number_of_rows = cursor.rowcount
        if number_of_rows > 0:
            for row in data:
                log.debug('[Crop: ' + str(raidNo) + ' (' + str(
                    self.uniqueHash) + ') ] ' + 'getRaidEndtime: Returning found endtime')
                log.debug(
                    '[Crop: ' + str(raidNo) + ' (' + str(self.uniqueHash) + ') ] ' + 'getRaidEndtime: Time: ' + str(
                        row[0]))
                return True, row[0]

        log.debug('[Crop: ' + str(raidNo) + ' (' + str(
            self.uniqueHash) + ') ] ' + 'getRaidEndtime: No matching endtime found')
        return False, None

    def raidExist(self, gym, type, raidNo):
        log.debug(
            '[Crop: ' + str(raidNo) + ' (' + str(self.uniqueHash) + ') ] ' + 'raidExist: Check DB for existing entry')
        # now = self.dbTimeStringToUnixTimestamp(str(datetime.datetime.now() - datetime.timedelta(hours=self.timezone)))
        now = time.time()
        try:
            connection = mysql.connector.connect(host=self.host,
                                                 user=self.user, port=self.port, passwd=self.password,
                                                 db=self.database)
        except:
            log.error("Could not connect to the SQL database")
            return False

        if type == "EGG":
            log.debug('[Crop: ' + str(raidNo) + ' (' + str(self.uniqueHash) + ') ] ' + 'raidExist: Check for EGG')
            cursor = connection.cursor()
            query = (' SELECT time_spawn FROM raids ' +
                     ' WHERE time_spawn >= ' + str(now) + ' and fort_id = \'' + str(gym) + '\'')
            log.debug(query)
            cursor.execute(query)
            data = cursor.fetchall()
            number_of_rows = cursor.rowcount
            if number_of_rows > 0:
                log.debug(
                    '[Crop: ' + str(raidNo) + ' (' + str(self.uniqueHash) + ') ] ' + 'raidExist: Found Rows: %s' % str(
                        number_of_rows))
                log.info('[Crop: ' + str(raidNo) + ' (' + str(
                    self.uniqueHash) + ') ] ' + 'raidExist: Egg already submitted - ignore new entry')
                return True

            log.info(
                '[Crop: ' + str(raidNo) + ' (' + str(self.uniqueHash) + ') ] ' + 'raidExist: Egg is new - submitting')
            return False
        else:
            log.debug('[Crop: ' + str(raidNo) + ' (' + str(self.uniqueHash) + ') ] ' + 'raidExist: Check for Mon')
            cursor = connection.cursor()
            query = (' SELECT count(*) FROM raids ' +
                     ' WHERE time_spawn <= ' + str(now) + ' and time_end >= ' + str(now) + ' and fort_id = \'' + str(
                        gym) + '\' and pokemon_id is not NULL')
            cursor.execute(query)
            data = cursor.fetchall()
            number_of_rows = cursor.rowcount
            if number_of_rows > 0:
                log.debug(
                    '[Crop: ' + str(raidNo) + ' (' + str(self.uniqueHash) + ') ] ' + 'raidExist: Found Rows: %s' % str(
                        number_of_rows))
                log.info('[Crop: ' + str(raidNo) + ' (' + str(
                    self.uniqueHash) + ') ] ' + 'raidExist: Mon already submitted - ignore new entry')
                return True

            log.info(
                '[Crop: ' + str(raidNo) + ' (' + str(self.uniqueHash) + ') ] ' + 'raidExist: Mon is new - submitting')
            return False

    def refreshTimes(self, gym, raidNo, captureTime):
        log.debug('[Crop: ' + str(raidNo) + ' (' + str(self.uniqueHash) + ') ] ' + 'Refresh Gym Times')

        # now = self.dbTimeStringToUnixTimestamp(str(datetime.datetime.now() - datetime.timedelta(hours=self.timezone)))
        now = time.time()
        try:
            connection = mysql.connector.connect(host=self.host,
                                                 user=self.user, port=self.port, passwd=self.password,
                                                 db=self.database)
        except:
            log.error("Could not connect to the SQL database")
            return False

        cursor = connection.cursor()
        query = (' update fort_sightings ' +
                 ' set last_modified = ' + str(now) + ', updated = ' + str(now) + ' where fort_id = \'' + gym + '\'')
        cursor.execute(query)
        connection.commit()

        return True

    def getNearGyms(self, lat, lng, hash, raidNo):
        try:
            connection = mysql.connector.connect(host=self.host,
                                                 user=self.user, port=self.port, passwd=self.password,
                                                 db=self.database)
        except:
            log.error("Could not connect to the SQL database")
            return []
        cursor = connection.cursor()

        query = ('SELECT ' +
                 ' id, ( ' +
                 ' 6371 * acos ( ' +
                 ' cos ( radians( \'' + str(lat) + '\' ) ) ' +
                 ' * cos( radians( lat ) ) ' +
                 ' * cos( radians( lon ) - radians( \'' + str(lng) + '\' ) ) ' +
                 ' + sin ( radians( \'' + str(lat) + '\' ) ) ' +
                 ' * sin( radians( lat ) ) ' +
                 ' ) ' +
                 ' ) AS distance ' +
                 ' FROM forts ' +
                 ' HAVING distance <= 2 ' +
                 ' ORDER BY distance')

        cursor.execute(query)

        data = []
        log.debug('[Crop: ' + str(raidNo) + ' (' + str(
            self.uniqueHash) + ') ] ' + 'getNearGyms: Result of NearGyms query: %s' % str(query))
        for (id) in cursor:
            data.append(id)

        log.debug(
            '[Crop: ' + str(raidNo) + ' (' + str(self.uniqueHash) + ') ] ' + 'getNearGyms: Closest Gyms: %s' % str(
                data))
        connection.commit()
        return data

    def setScannedLocation(self, lat, lng, captureTime):
        log.debug('setScannedLocation: not possible with monocle')
        return True

    def downloadDbCoords(self):
        try:
            connection = mysql.connector.connect(host=self.host,
                                                 user=self.user, port=self.port, passwd=self.password,
                                                 db=self.database)
        except:
            log.error("Could not connect to the SQL database")
            return False
        log.info('Downloading coords')
        lll = args.latlngleft
        llr = args.latlngright
        queryStr = ""
        if lll and llr:
            queryStr = ' where (lat BETWEEN {} AND {}) AND (lon BETWEEN {} AND {})'.format(lll[0], llr[0], lll[1],
                                                                                           llr[1])
        query = "SELECT lat, lon FROM forts {}".format(queryStr)
        cursor = connection.cursor()
        cursor.execute(query)
        file = open(args.file, 'w')
        for (lat, lon) in cursor:
            file.write(str(lat) + ', ' + str(lon) + '\n')
        cursor.close()
        connection.close()
        file.close()
        log.info('Downloading finished.')

    def __encodeHashJson(self, team_id, latitude, longitude, name, url):
        return (
            {'team_id': team_id, 'latitude': latitude, 'longitude': longitude, 'name': name, 'description': '',
             'url': url})

    def __download_img(self, url, file_name):
        retry = 1
        while retry <= 5:
            try:
                r = requests.get(url, stream=True, timeout=5)
                if r.status_code == 200:
                    with open(file_name, 'wb') as f:
                        r.raw.decode_content = True
                        shutil.copyfileobj(r.raw, f)
                    break
            except KeyboardInterrupt:
                log.info('Ctrl-C interrupted')
                sys.exit(1)
            except:
                retry = retry + 1
                log.info('Download error', url)
                if retry <= 5:
                    log.info('retry:', retry)
                else:
                    log.info('Failed to download after 5 retry')

    def downloadGymImages(self):
        try:
            connection = mysql.connector.connect(host=self.host,
                                                 user=self.user, port=self.port, passwd=self.password,
                                                 db=self.database)
        except:
            log.error("Could not connect to the SQL database")
            return False

        import json
        import io
        gyminfo = {}

        url_image_path = os.getcwd() + '/gym_img/'
        file_path = os.path.dirname(url_image_path)
        if not os.path.exists(file_path):
            os.makedirs(file_path)

        query = "SELECT forts.id, forts.lat, forts.lon, forts.name, forts.url FROM forts"
        cursor = connection.cursor()
        cursor.execute(query)

        for (id, lat, lon, name, url) in cursor:
            if url is not None:
                filename = url_image_path + '_' + str(id) + '_.jpg'
                print('Downloading', filename)
                self.__download_img(str(url), str(filename))
                gyminfo[id] = self.__encodeHashJson('0', lat, lon, name, url)
        cursor.close()
        connection.close()
        with io.open('gym_info.json', 'w', encoding='UTF-8') as outfile:
            outfile.write(unicode(json.dumps(gyminfo, indent=4, sort_keys=True)))
        return True
