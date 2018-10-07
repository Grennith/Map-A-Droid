#!/bin/bash
#############################################################################################
##                                EDIT                                                     ##
#############################################################################################
# This is where images and logs go to get packaged
#  make sure this directory is empty and only exists for this process
tmpdir="/tmp/madlogdig"
# This is where the packages end up
maddir="/tmp/madpackages"
#############################################################################################
##                              STOP EDITING                                               ##
#############################################################################################
help()
{
  cat <<EOF
Name:
     madlogdig - Script that digs through the Map-A-Droid log file
                 It will find any unknown raid timers, gyms, and mons
                 from your log file and attempt to package them for you.
                 You do not need root.

Synopsis:
     madlogdig.sh -f <log file>

Options:
     -h   - Help.  This message!
     -f   - Log file to scan

Example:
./madlogdig.sh -f logs/20180420_0420_0000.log
  This would scan the file given and give output similar to this:

There were 13 unknown raid timers, I packaged the 13 images that matched with them into /tmp/madpackages/utimers.tgz
There were 96 unknown mons, I packaged the 96 images that matched with them into /tmp/madpackages/umons.tgz
There were 23 unknown gyms, I packaged the 23 images that matched with them into /tmp/madpackages/ugyms.tgz
No unknown raidcounts
There were 1 dummy pics
There were 218 successful raids submitted

EOF
  exit 1
}
[ -z "$1" ] && help
while [ -n "$1" ]; do
case "$1" in
    -h) help;shift 1;;          # function help is called
    -f) logfile="$2";shift 2;;
    --) shift;break;; # end of options
     *) echo "error: no such option $1."; help;;
esac
done
  [ -z "$logfile" ] && echo "problem with log file" && help
! [ -e "$logfile" ] && echo "problem with log file" && help
mkdir -p "$tmpdir"
mkdir -p "$maddir"
rm "$tmpdir"/* "$maddir"/* 2>/dev/null

copyfile(){
while read -r filename _ ;do
 cp "$filename" "$tmpdir"/ 2>/dev/null && b=$((b+1))
 grep "$ts" "$logfile" > "$tmpdir/$(basename $filename.log)"
 c=$((c+1))
done < <(grep "$ts" "$logfile"|grep Filename|head -n1|awk -F']' '{print $5}'|awk -F':' '{print $3}')
}

packageimages(){
(cd "$tmpdir" && tar -zcf "$2.tgz" * && mv "$2.tgz" "$maddir"/ && rm *)
echo "There were $c $1, I packaged the $b images that matched with them into $maddir/$2.tgz"
}

thereisimages(){
ls "$tmpdir"/*.png 1>/dev/null 2>&1 && return 0
ls "$tmpdir"/*.jpg 1>/dev/null 2>&1 && return 0
return 1
}

unknowntimers(){
b=0
c=0
while read -r ts _ ;do
 copyfile
done < <(grep -B1 Useless "$logfile"|grep Crop|awk -F'(' '{print $2}'|awk -F')' '{print $1}')
if thereisimages ;then
 packageimages "unknown raid timers" "utimers"
elif (( c > 0 )) ;then
 if (( b == 0 )) ;then
  rm "$tmpdir"/*
 fi
 echo "There were $c unknown raid timers found but no images left to match them to"
else
 echo "No unknown raid timers"
fi
}

unknownmons(){
b=0
c=0
while read -r ts _ ;do
 copyfile
done < <(grep "Could not determine mon in crop" "$logfile"|awk -F'(' '{print $2}'|awk -F')' '{print $1}')
if thereisimages ;then
 packageimages "unknown mons" "umons"
elif (( c > 0 )) ;then
 if (( b == 0 )) ;then
  rm "$tmpdir"/*
 fi
 echo "There were $c unknown mons found but no images left to match them to"
else
 echo "No unknown mons"
fi
}

unknowngyms(){
b=0
c=0
while read -r ts _ ;do
 copyfile
done < <(grep "Could not determine gym" "$logfile"|awk -F'(' '{print $2}'|awk -F')' '{print $1}')
if thereisimages ;then
 packageimages "unknown gyms" "ugyms"
elif (( c > 0 )) ;then
 if (( b == 0 )) ;then
  rm "$tmpdir"/*
 fi
 echo "There were $c unknown gyms found but no images left to match them to"
else
 echo "No unknown gyms"
fi
}

unknownraidcount(){
b=0
c=0
while read -r filename _;do
 cp "$filename" "$tmpdir"/ 2>/dev/null && b=$((b+1))
 grep "$filename" "$logfile" > "$tmpdir/$(basename $filename.log)"
 c=$((c+1))
done < <(awk '/Could not read raidcount/{print $NF}' "$logfile")
if thereisimages ;then
 packageimages "unknown raidcounts" "uraidcounts"
elif (( c > 0 )) ;then
 if (( b == 0 )) ;then
  rm "$tmpdir"/*
 fi
 echo "There were $c unknown raidcounts found but no images left to match them to"
else
 echo "No unknown raidcounts"
fi
}

unknowntimers
unknownmons
unknowngyms
unknownraidcount
echo "There were $(grep 'start_detect: determine dummy pic, aborting analysis' "$logfile"|wc -l) dummy pics"
echo "There were $(grep successfound "$logfile"|wc -l) successful raids submitted"
