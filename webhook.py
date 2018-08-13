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


WH_PAYLOAD = """
    [{{
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
    
    if str(gymid) in data:
        name = data[str(gymid)]["name"]
        lat = data[str(gymid)]["latitude"]
        lon = data[str(gymid)]["longitude"]
    
    payload_raw = WH_PAYLOAD.format(
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
                type=type_)
    log.debug(payload_raw)
    payload = json.loads(payload_raw)
    response = requests.post(
                args.webhook_url, data=json.dumps(payload),
                headers={'Content-Type': 'application/json'}
            )
    
    
    
if __name__ == '__main__':
    send_webhook('0c4ddebbfdb44bd78cc3264e8c8c6232.1', 'EGG', '1534163280', '1534165980', '3', '004')
    
    
    