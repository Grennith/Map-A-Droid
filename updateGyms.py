import sys
import requests
import shutil
import mysql
import mysql.connector
import os
import time
import logging
from walkerArgs import parseArgs
from math import ceil, floor
import hashlib
import re

# encoding=utf8
import sys
reload(sys)
sys.setdefaultencoding('utf8')

args = parseArgs()

try:
    connection = mysql.connector.connect(host=args.dbip, user=args.dbusername, passwd=args.dbpassword, db=args.dbname)
except:
    print("Could not connect to the DB")
    exit(0)


def float_round(num, places=0, direction=floor):
    return direction(num * (10 ** places)) / float(10 ** places)


def updateEntry(gymName, lat, long, uri):
    if gymName.startswith('"') and gymName.endswith('"'):
        gymName = gymName[1:-1]
    if uri.startswith('"') and uri.endswith('"'):
        uri = uri[1:-1]
    print('Checking for existing gym and gymdetails entry')
    # gymName = "St. Dreifaltigkeit Krodorf" uri =
    # "https://lh4.ggpht.com/35FTQrG3D6Eyu4xY9tSYzY9867qe3bvVxAfmYXhYLrVQMEf3qOvm9B7OFnpxpiFlFA7-iJl1NaSji7MUsY_dAw"
    # lat = 50.627232 long = 8.631432

    latLow = float_round(lat, 3, floor)
    latHigh = float_round(lat, 3, ceil)
    longLow = float_round(long, 3, floor)
    longHigh = float_round(long, 3, ceil)

    print("Checking for gym in area of %s, %s, %s, %s" % (str(latLow), str(latHigh), str(longLow), str(longHigh)))

    queryStr = ("SELECT gym.gym_id, gym.latitude, gym.longitude, gymdetails.name, gymdetails.url FROM `gym` LEFT JOIN "
                "`gymdetails` ON gym.gym_id = gymdetails.gym_id WHERE latitude >= {} AND latitude <= {} AND "
                "longitude >= {} AND longitude <= {}").format(latLow, latHigh, longLow, longHigh)

    cursor = connection.cursor()
    cursor.execute(queryStr)
    # print len(list(cursor))
    # print cursor.rowcount
    rowCount = 0
    resultGym_id = None
    for (gym_id, latitude, longitude, name, url) in cursor:
        rowCount = + 1
        if name is None:
            print "WTF"
            print gym_id
        print("Found gym %s with name %s at %s, %s with imageURL %s" % (str(gym_id), str(name),
                                                                        str(latitude), str(longitude),
                                                                        str(url)))
        resultGym_id = gym_id

    cursor.close()
    print("Found %s entries" % str(rowCount))
    if rowCount > 1:
        print("Found more than one gym, aborting")
        return
    elif rowCount == 0 or resultGym_id is None:
        sha_1 = hashlib.sha1()
        sha_1.update(gymName + str(lat) + str(long))
        resultGym_id = sha_1.hexdigest()
        resultLatitude = lat
        resultLongitude = long
        print("Could not find gym, inserting gym with new ID %s" % resultGym_id)

        queryInsertGym = "INSERT INTO gym (gym_id, latitude, longitude) VALUES (\"{}\", {}, {})".format(resultGym_id,
                                                                                                        resultLatitude,
                                                                                                        resultLongitude)
        print("Using the following query: %s" % queryInsertGym)
        cursor = connection.cursor()
        cursor.execute(queryInsertGym)
        cursor.close()

    # the gym should now be in the DB, let's INSERT or UPDATE without a check
    queryInsertUpdateGymDetail = "INSERT INTO gymdetails (gym_id, name, url) VALUES (\"{}\", \"{}\", \"{}\") " \
                                 "ON DUPLICATE KEY UPDATE gym_id = \"{}\", name = \"{}\", url = \"{}\"".format(
        resultGym_id, gymName, uri, resultGym_id, gymName, uri
    )
    print("Calling query: %s" % queryInsertUpdateGymDetail)
    cursorSec = connection.cursor()
    cursorSec.execute(queryInsertUpdateGymDetail)
    cursorSec.close()
    connection.commit()


def main():
    content = None
    with open("updateGyms.txt") as f:
        content = f.readlines()
    # you may also want to remove whitespace characters like `\n` at the end of each line
    content = [x.strip() for x in content]
    for line in content:
        if len(line) < 5:
            continue
        values = re.split(''',(?=(?:[^'"]|'[^']*'|"[^"]*")*$)''', line)
        values = [x.strip() for x in values]
        if len(values) != 4:
            print("Line { %s } appears to be invalid" % str(values))
            continue
        if "name" in values[0]:
            # default first line, continue
            continue
        updateEntry(values[0], float(values[1]), float(values[2]), values[3])
        
    connection.close()
    sys.exit(0)


if __name__ == '__main__':
    main()
