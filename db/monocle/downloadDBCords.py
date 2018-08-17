import sys
import requests
import shutil
import mysql
import mysql.connector
import os
import time
import logging
from walkerArgs import parseArgs

args = parseArgs()

try:
    connection = mysql.connector.connect(host = args.dbip, user = args.dbusername, passwd = args.dbpassword, db = args.dbname)
except:
    print ("Keine Verbindung zum Server")
    exit(0)
    
    
def main():
    
    print('Downloading coords')
    lll = args.latlngleft
    llr = args.latlngright
    queryStr = ""
    if lll and llr:
        queryStr = ' where (lat BETWEEN {} AND {}) AND (lon BETWEEN {} AND {})'.format(lll[0], llr[0], lll[1], llr[1])
    query = ("SELECT lat, lon FROM forts {}").format(queryStr)
    cursor = connection.cursor()
    cursor.execute(query)
    file = open(args.file, 'w') 
    for (lat, lon) in cursor:
        file.write(str(lat) + ', ' + str(lon) + '\n') 
    cursor.close()
    connection.close()
    file.close()
    print('Downloading finished.')
    
if __name__ == '__main__':
    main()