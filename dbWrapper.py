import logging
import mysql
import mysql.connector
import datetime
import collections

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
            data.append((timestamp, RaidLocation(latitude, longitude)))

        connection.commit()
        return data
