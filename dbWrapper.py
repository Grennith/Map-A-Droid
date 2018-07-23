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

    def getNextRaidHatches(self):
        try:
            connection = mysql.connector.connect(host = self.host,
                user = self.user, port = self.port, passwd = self.password,
                db = self.database)
        except:
            log.error("Could not connect to the SQL database")
            return []
        cursor = connection.cursor()
        query = (' SELECT start, latitude, longitude FROM raid LEFT JOIN gym ' +
            'ON raid.gym_id = gym.gym_id WHERE raid.start >= \'%s\''
            % str(datetime.datetime.now() - datetime.timedelta(hours = self.timezone)))
        #print(query)
        #data = (datetime.datetime.now())
        cursor.execute(query)

        data = []
        for (start, latitude, longitude) in cursor:
            if latitude is None or longitude is None:
                continue
            timestamp = self.dbTimeStringToUnixTimestamp(str(start))
            #data.append((timestamp, RaidLocation(latitude, longitude)))
            #data.append((timestamp + 60, RaidLocation(latitude, longitude)))
            #data.append((timestamp + 2 * 60, RaidLocation(latitude, longitude)))
            #data.append((timestamp + 3 * 60, RaidLocation(latitude, longitude)))
            data.append((timestamp + 4 * 60, RaidLocation(latitude, longitude)))

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
            ' hash CHAR(255) NOT NULL, ' +
            ' type char(10) NOT NULL, ' +
            ' id CHAR(255) NOT NULL, ' +
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
        
    def submitRaid(self, gym, pkm, lvl, start, end, type):
        log.debug("Submitting raid")
        now = datetime.datetime.now()
        date1 = str(now.year) + "-0" + str(now.month) + "-" + str(now.day)
        today1 = date1 + " " + str(now.hour - (self.timezone)) + ":" + str(now.minute) + ":" + str(now.second)
        
        if self.raidExist(gym, type):
            log.debug('%s already submitted - ignoring' % str(type))
            return False

