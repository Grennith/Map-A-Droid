# -*- coding: utf-8 -*-

import threading
import logging
import time
from flask import (Flask, abort, jsonify, render_template,
                   request, make_response,
                   send_from_directory, send_file, redirect, current_app)
from walkerArgs import parseArgs
from db.dbWrapper import DbWrapper
import sys
import json
import os, glob, platform
import re
import datetime
from shutil import copyfile
from math import ceil, floor

app = Flask(__name__)

log = logging.getLogger(__name__)

args = parseArgs()

dbWrapper = DbWrapper(str(args.db_method), str(args.dbip), args.dbport, args.dbusername, args.dbpassword, args.dbname,
                      args.timezone)


#@app.before_first_request
#def init():
#    task = my_task.apply_async()
def run_job():
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        exit(0)


    t_webApp = threading.Thread(name='Web App', target=run_job)
    t_webApp.setDaemon(True)
    t_webApp.start()
        
@app.after_request
def after_request(response):
  response.headers.add('Access-Control-Allow-Origin', '*')
  response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
  response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
  return response

@app.route('/screens', methods=['GET'])
def screens():
    return render_template('screens.html', responsive = str(args.madmin_noresponsive).lower())

@app.route('/', methods=['GET'])
def root():
    return render_template('index.html')

@app.route('/raids', methods=['GET'])
def raids():
    return render_template('raids.html', sort = str(args.madmin_sort), responsive = str(args.madmin_noresponsive).lower())
    
@app.route('/gyms', methods=['GET'])
def gyms():
    return render_template('gyms.html', sort = args.madmin_sort, responsive = str(args.madmin_noresponsive).lower()) 

@app.route('/unknown', methods=['GET'])
def unknown():
    return render_template('unknown.html', responsive = str(args.madmin_noresponsive).lower()) 

@app.route('/map', methods=['GET'])
def map():
    return render_template('map.html')

@app.route("/submit_hash")
def submit_hash():
    hash = request.args.get('hash')
    id = request.args.get('id')

    if dbWrapper.insertHash(hash, 'gym', id, '999'):

        for file in glob.glob("www_hash/unkgym_*" + str(hash) + ".jpg"):
            copyfile(file, 'www_hash/gym_0_0_' + str(hash) + '.jpg')
            os.remove(file)

        return redirect("/unknown", code=302)

@app.route("/modify_raid_gym")
def modify_raid_gym():
    hash = request.args.get('hash')
    id = request.args.get('id')
    mon = request.args.get('mon')
    lvl = request.args.get('lvl')

    newJsonString = encodeHashJson(id, lvl, mon)
    dbWrapper.deleteHashTable('"' + str(hash) + '"', 'raid', 'in', 'hash')
    dbWrapper.insertHash(hash, 'raid', newJsonString, '999')

    return redirect("/raids", code=302)

@app.route("/modify_raid_mon")
def modify_raid_mon():
    hash = request.args.get('hash')
    id = request.args.get('gym')
    mon = request.args.get('mon')
    lvl = request.args.get('lvl')

    newJsonString = encodeHashJson(id, lvl, mon)
    dbWrapper.deleteHashTable('"' + str(hash) + '"', 'raid', 'in', 'hash')
    dbWrapper.insertHash(hash, 'raid', newJsonString, '999')

    return redirect("/raids", code=302)

@app.route("/modify_gym_hash")
def modify_gym_hash():
    hash = request.args.get('hash')
    id = request.args.get('id')

    dbWrapper.deleteHashTable('"' + str(hash) + '"', 'gym', 'in', 'hash')
    dbWrapper.insertHash(hash, 'gym', id, '999')

    return redirect("/gyms", code=302)

@app.route("/near_gym")
def near_gym():
    nearGym = []
    with open('gym_info.json') as f:
        data = json.load(f)
    lat = request.args.get('lat')
    lon = request.args.get('lon')
    if lat == "9999":
        distance = int(9999)
        lat = args.home_lat
        lon = args.home_lng
    else:
        distance = int(args.unknown_gym_distance)
    
    if not lat or not lon:
        return 'Missing Argument...'
    closestGymIds = dbWrapper.getNearGyms(lat, lon, 123, 1, int(distance))
    for closegym in closestGymIds:

        gymid = str(closegym[0])
        dist = str(closegym[1])
        gymImage = 'gym_img/_' + str(gymid)+ '_.jpg'

        name = 'unknown'
        lat = '0'
        lon = '0'
        url = '0'
        description = ''

        if str(gymid) in data:
            name = data[str(gymid)]["name"].replace("\\", r"\\").replace('"', '')
            lat = data[str(gymid)]["latitude"]
            lon = data[str(gymid)]["longitude"]
            if data[str(gymid)]["description"]:
                description = data[str(gymid)]["description"].replace("\\", r"\\").replace('"', '').replace("\n", "")

        ngjson = ({'id': gymid, 'dist': dist, 'name': name, 'lat': lat, 'lon': lon, 'description': description, 'filename': gymImage, 'dist': dist})
        nearGym.append(ngjson)

    return jsonify(nearGym)

@app.route("/delete_hash")
def delete_hash():
    nearGym = []
    hash = request.args.get('hash')
    type = request.args.get('type')
    redi = request.args.get('redirect')
    if not hash or not type:
        return 'Missing Argument...'

    dbWrapper.deleteHashTable('"' + str(hash) + '"', type, 'in', 'hash')
    for file in glob.glob("www_hash/*" + str(hash) + ".jpg"):
        os.remove(file)

    return redirect('/' + str(redi), code=302)

@app.route("/delete_file")
def delete_file():
    nearGym = []
    hash = request.args.get('hash')
    type = request.args.get('type')
    redi = request.args.get('redirect')
    if not hash or not type:
        return 'Missing Argument...'

    for file in glob.glob("www_hash/*" + str(hash) + ".jpg"):
        os.remove(file)

    return redirect('/' + str(redi), code=302)


@app.route("/get_gyms")
def get_gyms():
    gyms = []
    with open('gym_info.json') as f:
        data = json.load(f)

    hashdata = json.loads(getAllHash('gym'))

    for file in glob.glob("www_hash/gym_*.jpg"):
        unkfile = re.search('gym_(-?\d+)_(-?\d+)_((?s).*)\.jpg', file)
        hashvalue = (unkfile.group(3))

        if str(hashvalue) in hashdata:

            gymid =  hashdata[str(hashvalue)]["id"]
            count = hashdata[hashvalue]["count"]
            modify = hashdata[hashvalue]["modify"]

            creationdate = datetime.datetime.fromtimestamp(creation_date(file)).strftime('%Y-%m-%d %H:%M:%S')

            if args.madmin_time == "12":
                creationdate = datetime.datetime.strptime(creationdate, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %I:%M:%S %p')
                modify = datetime.datetime.strptime(modify, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %I:%M:%S %p')

            name = 'unknown'
            lat = '0'
            lon = '0'
            url = '0'
            description = ''

            gymImage = 'gym_img/_' + str(gymid)+ '_.jpg'

            if str(gymid) in data:
                name = data[str(gymid)]["name"].replace("\\", r"\\").replace('"', '')
                lat = data[str(gymid)]["latitude"]
                lon = data[str(gymid)]["longitude"]
                if data[str(gymid)]["description"]:
                    description = data[str(gymid)]["description"].replace("\\", r"\\").replace('"', '').replace("\n", "")

            gymJson = ({'id': gymid, 'lat': lat, 'lon': lon, 'hashvalue': hashvalue, 'filename': file, 'name': name, 'description': description, 'gymimage': gymImage, 'count': count, 'creation': creationdate, 'modify': modify })
            gyms.append(gymJson)

        else:
            print("File: " + str(file) + " not found in Database")
            os.remove(str(file))
            continue

    return jsonify(gyms)

@app.route("/get_raids")
def get_raids():
    raids = []
    eggIdsByLevel = [1, 1, 2, 2, 3]
    with open('gym_info.json') as f:
        data = json.load(f)

    with open('pokemon.json') as f:
        mondata = json.load(f)

    hashdata = json.loads(getAllHash('raid'))

    for file in glob.glob("www_hash/raid_*.jpg"):
        unkfile = re.search('raid_(-?\d+)_(-?\d+)_((?s).*)\.jpg', file)
        hashvalue = (unkfile.group(3))

        if str(hashvalue) in hashdata:
            monName = 'unknown'
            raidjson =  hashdata[str(hashvalue)]["id"]
            count = hashdata[hashvalue]["count"]
            modify = hashdata[hashvalue]["modify"]

            raidHash_ = decodeHashJson(raidjson)
            gymid = raidHash_[0]
            lvl = raidHash_[1]
            mon = int(raidHash_[2])
            monid = int(raidHash_[2])
            mon = "%03d"%mon


            if mon == '000':
                type = 'egg'
                monPic = ''
            else:
                type = 'mon'
                monPic = '/asset/pokemon_icons/pokemon_icon_' + mon + '_00.png'
                if str(monid) in mondata:
                    monName = mondata[str(monid)]["name"]

            eggId = eggIdsByLevel[int(lvl) - 1]
            if eggId == 1:
                eggPic = '/asset/static_assets/png/ic_raid_egg_normal.png'
            if eggId == 2:
                eggPic = '/asset/static_assets/png/ic_raid_egg_rare.png'
            if eggId == 3:
                eggPic = '/asset/static_assets/png/ic_raid_egg_legendary.png'

            creationdate = datetime.datetime.fromtimestamp(creation_date(file)).strftime('%Y-%m-%d %H:%M:%S')

            if args.madmin_time == "12":
                creationdate = datetime.datetime.strptime(creationdate, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %I:%M:%S %p')
                modify = datetime.datetime.strptime(modify, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %I:%M:%S %p')

            name = 'unknown'
            lat = '0'
            lon = '0'
            url = '0'
            description = ''

            gymImage = 'gym_img/_' + str(gymid)+ '_.jpg'

            if str(gymid) in data:
                name = data[str(gymid)]["name"].replace("\\", r"\\").replace('"', '')
                lat = data[str(gymid)]["latitude"]
                lon = data[str(gymid)]["longitude"]
                if data[str(gymid)]["description"]:
                    description = data[str(gymid)]["description"].replace("\\", r"\\").replace('"', '').replace("\n", "")

            raidJson = ({'id': gymid, 'lat': lat, 'lon': lon, 'hashvalue': hashvalue, 'filename': file, 'name': name, 'description': description, 'gymimage': gymImage, 'count': count, 'creation': creationdate, 'modify': modify,  'level': lvl, 'mon': mon, 'type': type, 'eggPic': eggPic, 'monPic': monPic, 'monname': monName })
            raids.append(raidJson)
        else:
            print("File: " + str(file) + " not found in Database")
            os.remove(str(file))
            continue

    return jsonify(raids)

@app.route("/get_mons")
def get_mons():
    mons = []
    monList =[]
    
    with open('pokemon.json') as f:
        mondata = json.load(f)
    
    with open('raidmons.json') as f:
        raidmon = json.load(f)
    
    for mons in raidmon:
        for mon in mons['DexID']:
            lvl = mons['Level']
            if str(mon).find("_") > -1:
                mon_split = str(mon).split("_")
                mon = mon_split[0]
                frmadd = mon_split[1] 
            else:
                frmadd = "00"

            mon = '{:03d}'.format(int(mon))
            
            monPic = '/asset/pokemon_icons/pokemon_icon_' + mon + '_00.png'
            monName = 'unknown'
            monid = int(mon)
            
            if str(monid) in mondata:
                monName = mondata[str(monid)]["name"]
            
            monJson = ({'filename': monPic, 'mon': monid, 'name': monName, 'lvl': lvl })
            monList.append(monJson)
            
    return jsonify(monList)

@app.route("/get_screens")
def get_screens():
    screens = []

    for file in glob.glob(str(args.raidscreen_path) + "/raidscreen_*.png"):
        creationdate = datetime.datetime.fromtimestamp(creation_date(file)).strftime('%Y-%m-%d %H:%M:%S')

        if args.madmin_time == "12":
            creationdate = datetime.datetime.strptime(creationdate, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %I:%M:%S %p')

        screenJson = ({'filename': file, 'creation': creationdate })
        screens.append(screenJson)


    return jsonify(screens)

@app.route("/get_unknows")
def get_unknows():
    unk = []
    for file in glob.glob("www_hash/unkgym_*.jpg"):
        unkfile = re.search('unkgym_(-?\d+\.?\d+)_(-?\d+\.?\d+)_((?s).*)\.jpg', file)
        creationdate = datetime.datetime.fromtimestamp(creation_date(file)).strftime('%Y-%m-%d %H:%M:%S')
        lat = (unkfile.group(1))
        lon = (unkfile.group(2))
        hashvalue = (unkfile.group(3))

        if args.madmin_time == "12":
            creationdate = datetime.datetime.strptime(creationdate, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %I:%M:%S %p')

        hashJson = ({'lat': lat, 'lon': lon,'hashvalue': hashvalue, 'filename': file, 'creation': creationdate})
        unk.append(hashJson)

    return jsonify(unk)


@app.route("/get_position")
def get_position():
    fileName = args.position_file+'.position'

    if not os.path.isfile(fileName):
        return jsonify([0, 0])

    with open(fileName) as f:
        latlon = f.read().strip().split(', ')
        if len(latlon) == 2:
            return jsonify([getCoordFloat(latlon[0]), getCoordFloat(latlon[1])])
        else:
            return jsonify([0, 0])


@app.route("/get_route")
def get_route():
    route = []

    with open(args.route_file+'.calc') as f:
        for line in f.readlines():
            latlon = line.strip().split(', ')
            route.append([
                getCoordFloat(latlon[0]),
                getCoordFloat(latlon[1])
            ])

    return jsonify(route)

@app.route("/get_gymcoords")
def get_gymcoords():
    coords = []

    with open('gym_info.json') as f:
        data = json.load(f)

        for gymid in data:
            gym = data[str(gymid)]
            coords.append({
                'id': gymid,
                'name': gym['name'],
                'img': gym['url'],
                'lat': gym['latitude'],
                'lon': gym['longitude']
                })

    return jsonify(coords)

@app.route('/gym_img/<path:path>', methods=['GET'])
def pushGyms(path):
    return send_from_directory('gym_img', path)

@app.route('/www_hash/<path:path>', methods=['GET'])
def pushHashes(path):
    return send_from_directory('www_hash', path)

@app.route('/screenshots/<path:path>', methods=['GET'])
def pushScreens(path):
    return send_from_directory(args.raidscreen_path, path)

@app.route('/match_unknows', methods=['GET'])
def match_unknows():
    hash = request.args.get('hash')
    lat = request.args.get('lat')
    lon = request.args.get('lon')
    return render_template('match_unknown.html', hash = hash, lat = lat, lon = lon, responsive = str(args.madmin_noresponsive).lower())

@app.route('/modify_raid', methods=['GET'])
def modify_raid():
    hash = request.args.get('hash')
    lat = request.args.get('lat')
    lon = request.args.get('lon')
    lvl = request.args.get('lvl')
    mon = request.args.get('mon')
    return render_template('change_raid.html', hash = hash, lat = lat, lon = lon, lvl = lvl, mon = mon, responsive = str(args.madmin_noresponsive).lower())

@app.route('/modify_gym', methods=['GET'])
def modify_gym():
    hash = request.args.get('hash')
    lat = request.args.get('lat')
    lon = request.args.get('lon')
    return render_template('change_gym.html', hash = hash, lat = lat, lon = lon, responsive = str(args.madmin_noresponsive).lower())

@app.route('/modify_mon', methods=['GET'])
def modify_mon():
    hash = request.args.get('hash')
    gym = request.args.get('gym')
    lvl = request.args.get('lvl')
    return render_template('change_mon.html', hash = hash, gym = gym, lvl = lvl, responsive = str(args.madmin_noresponsive).lower())

@app.route('/asset/<path:path>', methods=['GET'])
def pushAssets(path):
    return send_from_directory(args.pogoasset, path)


def decodeHashJson(hashJson):
    data = json.loads(hashJson)
    raidGym = data['gym']
    raidLvl = data["lvl"]
    raidMon = data["mon"]

    return raidGym, raidLvl, raidMon

def encodeHashJson(gym, lvl, mon):
    hashJson = json.dumps({'gym': gym, 'lvl': lvl, 'mon': mon}, separators=(',',':'))
    return hashJson

def getAllHash(type):
   rv = dbWrapper.getAllHash(type)
   hashRes = {}
   for result in rv:
       hashRes[result[1]]  = ({'id': str(result[0]), 'type': result[2], 'count': result[3], 'modify': str(result[4])})
   #data_json = json.dumps(hashRes, sort_keys=True, indent=4, separators=(',', ': '))
   data_json = hashRes
   return json.dumps(hashRes, indent=4, sort_keys=True)

def getCoordFloat(coordinate):
    return floor(float(coordinate) * (10 ** 5)) / float(10 ** 5)

def creation_date(path_to_file):
    """
    Try to get the date that a file was created, falling back to when it was
    last modified if that isn't possible.
    See http://stackoverflow.com/a/39501288/1709587 for explanation.
    """
    if platform.system() == 'Windows':
        return os.path.getctime(path_to_file)
    else:
        stat = os.stat(path_to_file)
        try:
            return stat.st_birthtime
        except AttributeError:
            # We're probably on Linux. No easy way to get creation dates here,
            # so we'll settle for when its content was last modified.
            return stat.st_mtime

if __name__ == "__main__":
    app.run()
    #host='0.0.0.0', port=int(args.madmin_port), threaded=False)

