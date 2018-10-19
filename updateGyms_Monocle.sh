#!/bin/bash
# This script expects your Monocle database in this format:
# https://raw.githubusercontent.com/whitewillem/PMSF/master/cleandb.sql
# If you just go into mysql and source that ^ file you will have a database named Monocle in the right format.

# You should have no reason to change these, it just feels weird hardcoding filenames
madconf=config.ini
gymfile=updateGyms.txt
errorfile=updateGyms.txt.error

! [[ -f "$madconf" ]] && echo "Unable to find your MAD config. You should be running the in the MAD directory" && exit 2
! [[ $(awk -F: '/^db_method/{print $2}' "$madconf"|awk -F'#' '{print $1}'|sed -e 's,[[:space:]]*$,,' -e 's,^[[:space:]]*,,') == monocle ]] && echo "the MAD config is not set to monocle and this script is only for monocle. Use updateGyms.py for RM" && exit 2

# Grab db info from MAD's config file
dbip=$(awk -F: '/^dbip/{print $2}' "$madconf"|awk -F'#' '{print $1}'|sed -e 's,[[:space:]]*$,,' -e 's,^[[:space:]]*,,')
user=$(awk -F: '/^dbusername/{print $2}' "$madconf"|awk -F'#' '{print $1}'|sed -e 's,[[:space:]]*$,,' -e 's,^[[:space:]]*,,')
pass=$(awk -F: '/^dbpassword/{print $2}' "$madconf"|awk -F'#' '{print $1}'|sed -e 's,[[:space:]]*$,,' -e 's,^[[:space:]]*,,')
db=$(awk -F: '/^dbname/{print $2}' "$madconf"|awk -F'#' '{print $1}'|sed -e 's,[[:space:]]*$,,' -e 's,^[[:space:]]*,,')
port=$(awk -F: '/^dbport/{print $2}' "$madconf"|awk -F'#' '{print $1}'|sed -e 's,[[:space:]]*$,,' -e 's,^[[:space:]]*,,')
[[ "$port" == "" ]] && port=3306
rm -f "$errorfile"

query(){
/usr/bin/mysql -N -B -u "$user" -D "$db" -p"$pass" -h "$dbip" -P "$port" -e "$1"
}

erroroutput(){
echo "Error inserting gym id $id: $name2"
echo "\"$name\", $lat, $lon, \"$url\", $test" >> "$errorfile"
}

id=$(( $(query "select id from forts order by id desc limit 1;") + 1 ))
gid=$(( $(query "select id from fort_sightings order by id desc limit 1;") + 1 ))
while IFS=, read -r name lat lon url test ;do
 ! [[ "$test" == "" ]] && echo "The line for $lat $lon has too many items in it, fix it and try again. Remember the quotes around name and url" && exit 2
 [[ "$lat" == "" ]] && continue
 name2=$(sed -e 's,[[:space:]]*$,,' -e 's,^[[:space:]]*,,' -e 's,^",,' -e 's,"$,,' <<< "$name")
 name=$(sed -e 's,[[:space:]]*$,,' -e 's,^[[:space:]]*,,' -e 's,^",,' -e 's,"$,,' -e "s,','',g" <<< "$name")
 url=$(sed -e 's,[[:space:]]*$,,' -e 's,^[[:space:]]*,,' -e 's,^",,' -e 's,"$,,' <<< "$url")
 while read dburl ;do
  [[ "$url" == "$dburl" ]] && echo "skipping $name2 because an entry with the same name and URL already exists" && continue 2
 done < <(query "select url from forts where name='$name'")
 echo "Inserting gym id $id: $name2"
 if query "insert into forts (id, external_id, lat, lon, name, url, sponsor, weather_cell_id, park, parkid, edited_by) values ($id,$id,$lat,$lon,'${name}','${url}', 0,NULL, NULL, NULL, NULL);" 2>/dev/null ;then
  query "insert into fort_sightings (id, fort_id, last_modified, team, guard_pokemon_id, slots_available, is_in_battle, updated) values ($gid,$id,1524212400,0,0,0,0,1524212400);" 2>/dev/null || erroroutput
 else erroroutput
 fi
 id=$(( 1 + $id ))
 gid=$(( 1 + $gid ))
done < <(grep --text -v "name,lat,lng,url" "$gymfile")

