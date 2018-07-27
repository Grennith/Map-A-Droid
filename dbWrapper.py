import logging
import mysql
import mysql.connector
import datetime
import collections
import datetime
import time

log = logging.getLogger(__name__)

RaidLocation = collections.namedtuple('RaidLocation', ['latitude', 'longitude'])


class DbWrapper:
    def __init__(self, host, port, user, password, database, timezone):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.timezone = timezone

    def dbTimeStringToUnixTimestamp(self, timestring):
        dt = datetime.datetime.strptime(timestring, '%Y-%m-%d %H:%M:%S')
        unixtime = (dt - datetime.datetime(1970, 1, 1)).total_seconds()
        return unixtime

    def getNextRaidHatches(self, delayAfterHatch):
        try:
            connection = mysql.connector.connect(host = self.host,
                user = self.user, port = self.port, passwd = self.password,
                db = self.database)
        except:
            log.error("Could not connect to the SQL database")
            return []
        cursor = connection.cursor()
        #query = (' SELECT start, latitude, longitude FROM raid LEFT JOIN gym ' +
        #    'ON raid.gym_id = gym.gym_id WHERE raid.start >= \'%s\''
        #    % str(datetime.datetime.now() - datetime.timedelta(hours = self.timezone)))
        query = (' SELECT start, latitude, longitude FROM raid LEFT JOIN gym ' +
            'ON raid.gym_id = gym.gym_id WHERE raid.start >= raid.last_scanned ' +
            'AND raid.end > \'%s\'' % str(datetime.datetime.now() - datetime.timedelta(hours = self.timezone)))
        #print(query)
        #data = (datetime.datetime.now())
        cursor.execute(query)

        data = []
        for (start, latitude, longitude) in cursor:
            if latitude is None or longitude is None:
                continue
            timestamp = self.dbTimeStringToUnixTimestamp(str(start))
            data.append((timestamp + delayAfterHatch * 60, RaidLocation(latitude, longitude)))

        connection.commit()
        return data

    def createHashDatabaseIfNotExists(self):
        log.debug('Creating hash db in database')
        try:
            connection = mysql.connector.connect(host = self.host,
                user = self.user, port = self.port, passwd = self.password,
                db = self.database)
        except:
            log.error("Could not connect to the SQL database")
            return False
        cursor = connection.cursor()
        query = (' Create table if not exists trshash ( ' +
            ' hashid MEDIUMINT NOT NULL AUTO_INCREMENT, ' +
            ' hash VARCHAR(255) NOT NULL, ' +
            ' type VARCHAR(10) NOT NULL, ' +
            ' id VARCHAR(255) NOT NULL, ' +
            ' PRIMARY KEY (hashid))' )
        log.debug(query)
        cursor.execute(query)
        connection.commit()
        return True

    def checkForHash(self, hash, type):
        log.debug('Checking for hash in db')
        try:
            connection = mysql.connector.connect(host = self.host,
                user = self.user, port = self.port, passwd = self.password,
                db = self.database)
        except:
            log.error("Could not connect to the SQL database")
            return None
        cursor = connection.cursor()
        query = (' SELECT id FROM trshash ' +
                'WHERE type = \'%s\' and hash = \'%s\''
                % (str(type), str(hash)))
        log.debug(query)

        cursor.execute(query)
        id = None
        for (id) in cursor:
            if id is None:
                return None
            else:
                log.debug("checkForHash: Found hash %s" % str(id[0]))
                return id[0]

    def insertHash(self, hash, type, id):
        try:
            connection = mysql.connector.connect(host = self.host,
            user = self.user, port = self.port, passwd = self.password,
            db = self.database)
        except:
           log.error("Could not connect to the SQL database")
           return False
        cursor = connection.cursor()
        query = (' INSERT INTO trshash ' +
              ' ( hash, type, id ) VALUES ' +
              ' (\'%s\', \'%s\', \'%s\')'
              % (str(hash), str(type), str(id)))
        log.debug(query)
        cursor.execute(query)
        connection.commit()
        return True

    def deleteHashTable(self, ids, type):
        log.debug('Deleting old Hashes of type %s' % type)
        log.debug('Valid ids: %s' %  ids)
        try:
            connection = mysql.connector.connect(host = self.host,
            user = self.user, port = self.port, passwd = self.password,
            db = self.database)
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

    def submitRaid(self, gym, pkm, lvl, start, end, type, MonWithNoEgg=False):
        log.debug("Submitting raid")
        zero = datetime.datetime.now()
        zero =  time.mktime(zero.timetuple())
        now_timezone = datetime.datetime.now()
        now_timezone =  time.mktime(now_timezone.timetuple()) - (self.timezone * 60 * 60)
        now = datetime.datetime.now()
        date1 = str(now.year) + "-0" + str(now.month) + "-" + str(now.day)
        today1 = date1 + " " + str(now.hour - (self.timezone)) + ":" + str(now.minute) + ":" + str(now.second)

        if self.raidExist(gym, type):
            self.refreshTimes(gym)
            log.debug('%s already submitted - ignoring' % str(type))
            return True

        try:
            connection = mysql.connector.connect(host = self.host,
            user = self.user, port = self.port, passwd = self.password,
            db = self.database)
        except:
            log.error("Could not connect to the SQL database")
            return False

        cursor = connection.cursor()
        log.debug("Submitting something of type %s" % type)
        if type == 'EGG':
            #query = " UPDATE raid SET level = %s, spawn=FROM_UNIXTIME(%s), start=FROM_UNIXTIME(%s), end=FROM_UNIXTIME(%s), pokemon_id = %s, cp = %s, move_1 = %s, move_2 = %s, last_scanned = %s WHERE gym_id = %s "
            #data = (lvl, start, start, end, monegg[int(lvl) - 1], "999", "1", "1",  today1, guid)
            log.info("Submitting Egg. Gym: %s, Lv: %s, Start and Spawn: %s, End: %s, last_scanned: %s" % (gym, lvl, start, end, today1))
            query = (' INSERT INTO raid (gym_id, level, spawn, start, end, pokemon_id, cp, move_1, ' +
                'move_2, last_scanned) VALUES(%s, %s, FROM_UNIXTIME(%s), FROM_UNIXTIME(%s), ' +
                'FROM_UNIXTIME(%s), %s, %s, %s, %s, FROM_UNIXTIME(%s)) ON DUPLICATE KEY UPDATE level = %s, ' +
                'spawn=FROM_UNIXTIME(%s), start=FROM_UNIXTIME(%s), end=FROM_UNIXTIME(%s), ' +
                'pokemon_id = %s, cp = %s, move_1 = %s, move_2 = %s, last_scanned = FROM_UNIXTIME(%s)')  
            data = (gym, lvl, start, start, end, None, "999", "1", "1", now_timezone, #TODO: check None vs null?
                lvl, start, start, end, None, "999", "1", "1", now_timezone)
            #data = (lvl, start, start, end, None, "999", "1", "1", today1, guid)
            cursor.execute(query, data)  
        else:
            log.info("Submitting mon. PokemonID %s, Lv %s, last_scanned %s, gymID %s" % (pkm, lvl, today1, gym))
            if not MonWithNoEgg:
                query = " UPDATE raid SET pokemon_id = %s, cp = %s, move_1 = %s, move_2 = %s, last_scanned = FROM_UNIXTIME(%s) WHERE gym_id = %s "
                data = (pkm, "999", "1", "1",  now_timezone, gym)
            else:
                query = (' INSERT INTO raid (gym_id, level, spawn, start, end, pokemon_id, cp, move_1, ' +
                    'move_2, last_scanned) VALUES(%s, %s, FROM_UNIXTIME(%s), FROM_UNIXTIME(%s), ' +
                    'FROM_UNIXTIME(%s), %s, %s, %s, %s, FROM_UNIXTIME(%s)) ON DUPLICATE KEY UPDATE level = %s, ' +
                    'spawn=FROM_UNIXTIME(%s), start=FROM_UNIXTIME(%s), end=FROM_UNIXTIME(%s), ' +
                    'pokemon_id = %s, cp = %s, move_1 = %s, move_2 = %s, last_scanned = FROM_UNIXTIME(%s)')  
                data = (gym, lvl, int(zero)-10000, int(zero)-10000, end, pkm, "999", "1", "1", now_timezone, #TODO: check None vs null?
                    lvl, int(zero)-10000, int(zero)-10000, end, pkm, "999", "1", "1", now_timezone)
                
            cursor.execute(query, data)

        connection.commit()
        
        self.refreshTimes(gym)
        
        return True
        
    def readRaidEndtime(self, gym):
        log.debug('Check DB for existing mon')
        now = (datetime.datetime.now() - datetime.timedelta(hours = self.timezone)).strftime("%Y-%m-%d %H:%M:%S")
        log.debug(now)
        try:
            connection = mysql.connector.connect(host = self.host,
            user = self.user, port = self.port, passwd = self.password,
            db = self.database)
        except:
            log.error("Could not connect to the SQL database")
            return False
            
        cursor = connection.cursor()
        query = (' SELECT count(*) FROM raid ' +
            ' WHERE STR_TO_DATE(raid.end,\'%Y-%m-%d %H:%i:%s\') >= STR_TO_DATE(\'' + str(now) + '\',\'%Y-%m-%d %H:%i:%s\') and gym_id = \'' + str(gym) + '\'')
        log.debug(query)
        cursor.execute(query)
        result=cursor.fetchone()
        number_of_rows=result[0]
        log.debug('Found Rows: %s' % str(number_of_rows))
        rows_affected=number_of_rows

        if rows_affected > 0:
            log.info("Endtime already submitted")
            return True

        log.info('Endtime is new - submitting')
        return False
        

    def raidExist(self, gym, type):
        log.debug('Check DB for existing entry')
        now = (datetime.datetime.now() - datetime.timedelta(hours = self.timezone)).strftime("%Y-%m-%d %H:%M:%S")
        log.debug(now)
        try:
            connection = mysql.connector.connect(host = self.host,
            user = self.user, port = self.port, passwd = self.password,
            db = self.database)
        except:
            log.error("Could not connect to the SQL database")
            return False

        if type == "EGG":
            log.debug('Check for EGG')
            cursor = connection.cursor()
            query = (' SELECT count(*) FROM raid ' +
                ' WHERE STR_TO_DATE(raid.start,\'%Y-%m-%d %H:%i:%s\') >= STR_TO_DATE(\'' + str(now) + '\',\'%Y-%m-%d %H:%i:%s\') and gym_id = \'' + str(gym) + '\'')
            log.debug(query)
            cursor.execute(query)
            result=cursor.fetchone()
            number_of_rows=result[0]
            log.debug('Found Rows: %s' % str(number_of_rows))
            rows_affected=cursor.rowcount

            if number_of_rows > 0:
                log.info("Egg already submitted - ignore new entry")
                return True

            log.info('Egg is new - submitting')
            return False
        else:
            log.debug('Check for Mon')
            cursor = connection.cursor()
            query = (' SELECT count(*) FROM raid ' +
                ' WHERE STR_TO_DATE(raid.start,\'%Y-%m-%d %H:%i:%s\') <= STR_TO_DATE(\'' + str(now) + '\',\'%Y-%m-%d %H:%i:%s\') and STR_TO_DATE(raid.end,\'%Y-%m-%d %H:%i:%s\') >= STR_TO_DATE(\'' + str(now) + '\',\'%Y-%m-%d %H:%i:%s\') and gym_id = \'' + str(gym) + '\' and pokemon_id is not NULL')
            log.debug(query)
            cursor.execute(query)
            result=cursor.fetchone()
            number_of_rows=result[0]
            log.debug('Found Rows: %s' % str(number_of_rows))
            rows_affected=number_of_rows

            if rows_affected > 0:
                log.info("Mon already submitted - ignore new entry")
                return True

            log.info('Mon is new - submitting')
            return False
            
    def refreshTimes(self, gym):
        log.debug('Refresh Gym Times')
        now = (datetime.datetime.now() - datetime.timedelta(hours = self.timezone)).strftime("%Y-%m-%d %H:%M:%S")
        now_timezone = datetime.datetime.now()
        now_timezone =  time.mktime(now_timezone.timetuple()) - (self.timezone * 60 * 60)
        log.debug(now)
        try:
            connection = mysql.connector.connect(host = self.host,
            user = self.user, port = self.port, passwd = self.password,
            db = self.database)
        except:
            log.error("Could not connect to the SQL database")
            return False
            
        cursor = connection.cursor()
        query = (' update gym ' +
            ' set last_modified = \'' + str(now) + '\', last_scanned = \'' + str(now) + '\' where gym_id = \'' + gym + '\'')
        log.debug(query)
        cursor.execute(query)
        query = (' update raid ' +
            ' set last_scanned = FROM_UNIXTIME(\'' + str(now_timezone) + '\') where gym_id = \'' + gym + '\'')
        log.debug(query)
        cursor.execute(query)
        connection.commit()

        return True
