import sys
import requests
import shutil
import mysql;
import mysql.connector;
import os
import time
import logging

log = logging.getLogger(__name__)

class FortImageDownloader:
    def __init__(self, dbIp, dbPort, dbUser, dbPassword, dbName):
        self.dbIp = dbIp
        self.dbPort = dbPort
        self.dbUser = dbUser
        self.dbPassword = dbPassword
        self.dbName = dbName

        if not os.path.exists('gym_img'):
            log.info('gym_im directory created')
            os.makedirs('gym_im')

        self.url_image_path = os.getcwd() + '/gym_img/'

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
                print('Ctrl-C interrupted')
                session.close()
                sys.exit(1)
            except:
                retry=retry+1
                print('Download error', url)
                if retry <= 5:
                    print('retry:', retry)
                else:
                    print('Failed to download after 5 retry')

    def downloadImages(self):
        try:
            connection = mysql.connector.connect(host = self.dbIp, user = self.dbUser, passwd = self.dbPassword, db = self.dbName, port = self.dbPort)
        except:
            print ("Keine Verbindung zum Server")
            exit(0)
        file_path = os.path.dirname(url_image_path)
        if not os.path.exists(file_path):
            os.makedirs(file_path)

        query = ("SELECT gym_id, url FROM gymdetails")
        cursor = connection.cursor()
        cursor.execute(query)

        for (gym_id, url) in cursor:
            if url is not None:
                filename = url_image_path + '_' + str(gym_id) + '_.jpg'
                print('Downloading', filename)
                self.__download_img(str(url), str(filename))
        cursor.close()
        connection.close()
