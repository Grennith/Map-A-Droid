import sys
import requests
import shutil
import mysql;
import mysql.connector;
import os
import time
import logging
from walkerArgs import parseArgs

log = logging.getLogger(__name__)

if not os.path.exists('gym_img'):
    log.info('gym_im directory created')
    os.makedirs('gym_img')

url_image_path = os.getcwd() + '/gym_img/'


args = parseArgs()

try:
    log.error(args.dbip)
    log.error(args.dbusername)
    log.error(args.dbpassword)
    log.error(args.dbname)
    connection = mysql.connector.connect(host = args.dbip, user = args.dbusername, passwd = args.dbpassword, db = args.dbname)
except:
    print ("Keine Verbindung zum Server")
    exit(0)

def download_img(url, file_name):
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

def main():

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
            download_img(str(url), str(filename))
    cursor.close()
    connection.close()

if __name__ == '__main__':
    main()
