Configuration & Running
=======================

.. contents:: :local:

Config
------

1. Rename `config.ini.example` to `config.ini` and fill out:
- Screen Method (Set it to 0)
- MySQL Settings (RM or Moncole Database)
- Device Specifics (Width and Height resolutions in pixels)
- Path Settings (pogoasset only)
- Timezone Settings
- Coords CSV (Create a blank "coords.csv" file and set `file: coords.csv`)


Get Gym Images
--------------
2) We need gym images and there are two solutions:
- If you have a RocketMap/Monocle database with old gym-details, run `downloadfortimg.py`
- Or, grab the images from `Ingress Intel Map <https://www.ingress.com/intel>`_

(The images should be located in `gym_img` folder)


Get Gym Coords
--------------
3) We also need gym locations and there are two solutions:
- If you have a RocketMap/Monocle database with old gym-details, run `downloadDBCords.py`
- Or, grab the locations from `Ingress Intel Map <https://www.ingress.com/intel>`_

(The coords should be located in `coords.csv` if you followed the last step in 1.)

4) Fill out the rest of the `config.ini`, the important parts are:
- Telnet Settings (RemoteGpsController)

Running
-------

1. Mobile - Start Remote GPS Controller.
* Select Start within the app to start GPS
* Select MediaProjection to allow touch commands

2. PC - Make sure you're in the directory of Map-A-Droid and run the following 2 commands

To start the GPS walking around
`python startWalker.py -os`

To start the processing of the screenshot that have been taken
`python startWalker.py -oo`

Best practice is to run both commands in seperate `screen <https://www.gnu.org/software/screen/>`_ sessions.

>Note if running via ssh you may face issues around "no screen available" to get around the prefix your commands with `MPLBACKEND=Agg`
