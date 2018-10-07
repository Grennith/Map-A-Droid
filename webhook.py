import logging
from walkerArgs import parseArgs
import requests
import json
import sys
from s2sphere import Cell, CellId, LatLng

reload(sys)

sys.setdefaultencoding('utf8')

log = logging.getLogger(__name__)
args = parseArgs()

raid_webhook_payload = """[{{
      "message": {{
        "latitude": {lat},
        "longitude": {lon},
        "level": {lvl},
        "pokemon_id": "{poke_id}",
        "team": {team},
        "cp": "{cp}",
        "move_1": {move_1},
        "move_2": {move_2},
        "raid_begin": {hatch_time},      
        "raid_end": {end},
        "gym_id": "{ext_id}",
        "name": "{name_id}",
        "gym_url": "{url}",
        "sponsor": "{sponsor}",
        "weather": "{weather}",
        "park": "{park}"
      }},
      "type": "{type}"
   }} ]"""


egg_webhook_payload = """[{{
      "message": {{
        "latitude": {lat},
        "longitude": {lon},
        "level": {lvl},
        "team": {team},
        "raid_begin": {hatch_time},      
        "raid_end": {end},
        "gym_id": "{ext_id}",
        "name": "{name_id}",
        "gym_url": "{url}",
        "sponsor": "{sponsor}",
        "weather": "{weather}",
        "park": "{park}"
      }},
      "type": "{type}"
   }} ]"""


def get_raid_boss_cp(mon_id):
    if int(mon_id) > 0:
        with open('pokemon.json') as j:
            pokemon_file = json.load(j)

        log.debug("Removing leading zero from string where necessary")
        mon_id = int(mon_id)

        if 'cp' in pokemon_file[str(mon_id)]:
            log.debug("CP found for pokemon_id: " + str(mon_id) + " with the value of " + str(
                pokemon_file[str(mon_id)]["cp"]))
            return pokemon_file[str(mon_id)]["cp"]
        else:
            log.warning("No raid cp found for " + str(mon_id))
            return '0'
    else:
        log.debug("No CP returns as its an egg!")
        return '0'


def send_raid_webhook(gymid, type, start, end, lvl, mon=0):
    log.info('Start preparing values for web hook')

    if mon is None:
        poke_id = 0
    else:
        poke_id = mon

    log.debug('poke_id: ' + str(poke_id))
    gym_id = gymid
    log.debug('gym_id: ' + str(gym_id))
    move_1 = '1'
    log.debug('move_1: ' + str(move_1))
    move_2 = '1'
    log.debug('move_2: ' + str(move_2))
    cp = get_raid_boss_cp(poke_id)
    log.debug('cp: ' + str(cp))
    lvl = lvl
    log.debug('lvl: ' + str(lvl))
    hatch_time = int(start)
    log.debug('hatch_time: ' + str(hatch_time))
    end = int(end)
    log.debug('end: ' + str(end))
    form = '0'
    log.debug('form: ' + str(form))
    team = '0'
    log.debug('team: ' + str(team))
    type_ = 'raid'
    log.debug('type_: ' + str(type_))
    sponsor = '0'
    log.debug('sponsor: ' + str(sponsor))
    weather = '0'
    log.debug('weather: ' + str(weather))
    park = 'unknown'
    log.debug('park: ' + str(park))

    with open('gym_info.json') as f:
        data = json.load(f)

    name = 'unknown'
    log.debug('name: ' + str(name))
    lat = '0'
    log.debug('lat: ' + str(lat))
    lon = '0'
    log.debug('lon: ' + str(lon))
    url = '0'
    log.debug('url: ' + str(url))
    description = ''
    log.debug('description: ' + str(description))

    if str(gymid) in data:
        name = data[str(gymid)]["name"].replace("\\", r"\\").replace('"', '')
        log.debug('data_name: ' + str(name))
        lat = data[str(gymid)]["latitude"]
        log.debug('data_lat: ' + str(end))
        lon = data[str(gymid)]["longitude"]
        log.debug('data_lat: ' + str(end))
        url = data[str(gymid)]["url"]
        log.debug('data_url: ' + str(end))
        if data[str(gymid)]["description"]:
            description = data[str(gymid)]["description"].replace("\\", r"\\").replace('"', '').replace("\n", "")
            log.debug('data_description: ' + str(description))
        if 'park' in data[str(gymid)]:
            park = data[str(gymid)]["park"]
            log.debug('data_park: ' + str(park))
        if 'sponsor' in data[str(gymid)]:
            sponsor = data[str(gymid)]["sponsor"]
            log.debug('data_sponsor: ' + str(sponsor))

    if args.webhook:
        if poke_id == 0 or poke_id is None:
            payload_raw = egg_webhook_payload.format(
                ext_id=gym_id,
                lat=lat,
                lon=lon,
                name_id=name,
                sponsor=sponsor,
                lvl=lvl,
                end=end,
                hatch_time=hatch_time,
                team=team,
                type=type_,
                url=url,
                description=description,
                park=park,
                weather=weather
            )
        else:
            payload_raw = raid_webhook_payload.format(
                ext_id=gym_id,
                lat=lat,
                lon=lon,
                name_id=name,
                sponsor=sponsor,
                poke_id=poke_id,
                lvl=lvl,
                end=end,
                hatch_time=hatch_time,
                move_1=move_1,
                move_2=move_2,
                cp=cp,
                form=form,
                team=team,
                type=type_,
                url=url,
                description=description,
                park=park,
                weather=weather
            )

        log.debug(payload_raw)

        payload = json.loads(payload_raw)
        response = requests.post(
            args.webhook_url, data=json.dumps(payload),
            headers={'Content-Type': 'application/json'}
        )



weather_webhook_payload = """[{{
      "message": {{
                "s2_cell_id": {0},
                "coords": {1},
                "condition": {2},
                "alert_severity": {3},
                "warn": {4},
                "day": {5},
                "time_changed": {6}
        }},
      "type": "weather"
   }} ]"""


def send_weather_webhook(s2cellId, weatherId, severe, warn, day, time):
    if args.weather_webhook:
        log.debug("Send Weather Webhook")

        cell = Cell(CellId(s2cellId))
        coords = []
        for v in range(0, 4):
            vertex = LatLng.from_point(cell.get_vertex(v))
            coords.append([vertex.lat().degrees, vertex.lng().degrees])

        data = weather_webhook_payload.format(s2cellId, coords, weatherId, severe, warn, day, time)

        log.debug(data)
        payload = json.loads(data)
        response = requests.post(
            args.webhook_url, data=json.dumps(payload),
            headers={'Content-Type': 'application/json'}
        )
    else:
        log.debug("Weather Webhook Disabled")



if __name__ == '__main__':
    send_raid_webhook('33578092c5554275a589bd1e144bbbcc.16', 'EGG', '1534163280', '1534165980', '5', 004)
