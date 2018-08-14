import logging
from walkerArgs import parseArgs
import requests
import json
import datetime
import time
import sys
reload(sys)


sys.setdefaultencoding('utf8')

log = logging.getLogger(__name__)
args = parseArgs()

webhook_payload = {}


webhook_payload['other'] =     """[{{
      "message": {{
        "name": "{name_id}",
        "latitude": {lat},
        "longitude": {lon},
        "level": {lvl},
        "pokemon_id": {poke_id},
        "raid_end": {end},
        "raid_begin": {hatch_time},
        "cp": {cp},
        "move_1": {move_1},
        "move_2": {move_2},
        "gymid": "{ext_id}",
        "team": {team}
      }},
      "type": "{type}"
   }} ]"""


webhook_payload['PA_gyminfos'] = """
    [{{
      "message": {{
        "name": "{name_id}",
        "url": "{url}",
        "description": "{description}",
        "latitude": {lat},
        "longitude": {lon},
        "id": "{ext_id}",
        "team": {team}
      }},
      "type": "gym_details"
   }} ]
"""

webhook_payload['PA_raid'] = """
    [{{
      "message": {{
        "latitude": {lat},
        "longitude": {lon},
        "level": {lvl},
        "pokemon_id": {poke_id},
        "end": {end},
        "start": {hatch_time},
        "cp": {cp},
        "move_1": {move_1},
        "move_2": {move_2},
        "gym_id": "{ext_id}"
      }},
      "type": "raid"
   }} ]
"""

def send_webhook(gymid, type, start, end, lvl, mon=0):
    
    gym_id = gymid
    move_1 = '1'
    move_2 = '1'
    cp = '999'
    lvl = lvl
    cp = '999'
    poke_id = int(mon)
    hatch_time = int(start)
    end = int(end)
    form = '0'
    team = '0'
    type_ = type
    sponsor = '0'
    
    with open('gym_info.json') as f:
        data = json.load(f)
        
    name = 'unknown'
    lat = '0'
    lon = '0'
    url = '0'
    description = ''
    
    if str(gymid) in data:
        name = data[str(gymid)]["name"].replace("\\", r"\\").replace('"', '')
        lat = data[str(gymid)]["latitude"]
        lon = data[str(gymid)]["longitude"]
        url = data[str(gymid)]["url"]
        if data[str(gymid)]["description"]:
            description = data[str(gymid)]["description"].replace("\\", r"\\").replace('"', '')
    
    for whtyp in args.webhook_type:
        log.debug('Using WH Type: ' + str(whtyp))
    
        payload_raw = webhook_payload[whtyp].format(
                ext_id=gymid,
                lat=lat,
                lon=lon,
                name_id=name,
                sponsor=sponsor,
                poke_id=poke_id,
                lvl=lvl,
                end=end,
                hatch_time=end-2700,
                move_1 = move_1,
                move_2 = move_2,
                cp = cp,
                form = form,
                team = team,
                type=type_,
                url=url,
                description=description
                )

        payload = json.loads(payload_raw)
        response = requests.post(
                args.webhook_url, data=json.dumps(payload),
                headers={'Content-Type': 'application/json'}
            )
    
    
    
if __name__ == '__main__':
    send_webhook('0c4ddebbfdb44bd78cc3264e8c8c6232.16', 'EGG', '1534163280', '1534165980', '3', '004')
    
    
    