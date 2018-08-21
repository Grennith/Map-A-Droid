# The Raid Mapper

The Raid Mapper is a raid scanner for Pokemon GO based on Android devices.
It consists of two parts:
1) OCR
2) Scan

The result is a map (RocketMap to be precise) filled with Raidbosses or Eggs with their Name and Tier.
Example screen #TODO

# Requirements
#### General
1) A computer (RaspberryPI likely is sufficient as well)
2) A RM DB with gymdetails for the gyms you intend to scan (you can download the gym images with those details...). Alternative: Get the ingress images of the gyms you want to scan...

#### OCR
The OCR part requires screenshots to come in. If you already have RDRM (Real Device Raid Mapper) running, you could use the OCR part to send information to RM.
1) [PoGoAssets](https://github.com/ZeChrales/PogoAssets)
2) Mons need to not have been seen. Get yourself a fresh account without even T1 mons

#### Scan
1) Android 8.0 (API 26) or higher
2) Root privileges (Magisk) and flashing [Terminal APP Systemizer](https://forum.xda-developers.com/apps/magisk/module-terminal-app-systemizer-ui-t3585851)
3) VNC app and RemoteGpsController.apk (the latter requires System privileges)

We provide a VNC app which is based on [droidVNC](https://github.com/oNaiPs/droidVncServer).
> The app is not stable. We had it running for weeks and it would just give up for a whole day. We are planning on releasing our very own app.
As Stupid as it may sound, an apparent workaround might be:
Start droidVNC, start Server, switch out of app and go to System Settings -> Apps -> droidVNC -> Force stop. The server itself should continue running.

### Current limitations
1) For the moment: 9:16 aspect ratio Smartphones only. If you got a softkey bar, disable it for pogo.
2) VNC app apparently can have hick-ups....
3) Teleporting from location to location takes the game to load images. Faster phones may handle it better. We are testing on low end specs (Redmi 5A for 75 bucks). We will likely add a parameter to set the delays inbetween teleports and screenshots.
4) Sometimes mons do not get reported to the DB. We are in the process of debugging. It can help to remove the files in the hash-folder however.

# Installation on Server/Desktop
1) Install python according to docs for your platform.

  Having installed python, do get yourself python pip and run
  `pip install -r requirements.txt`

  Depending on your OS, you probably need to install some more stuff.
  E.g. Ubuntu/Debian requires you to run
  ```bash
  sudo apt update
  sudo apt install tesseract-ocr python-opencv
  ```
2) Create a .csv with coords of gyms (one coord per line in format 'lat,lng'):
  ```bash
  lat1,lng1
  lat2,lng2
  ...etc
  ```
  You can also try to download the coords of gyms from your existing RM DB (downloadDBCords.py)
3) Insert gym images into gym_img folder. Either manually (e.g. from Ingress) or
  try the downloadfortimg.py
4) Configure config.ini as needed. See `config.ini.example` for params and info
5) Start TRM by calling `python startWalker.py`

For performance it might be worth giving ocr_multitask a chance and/or calling
startWalker.py with `-os` in one console and `-oo` in another.


# Steps on Android device
1) Install Pogo, droidVNC, RemoteGpsController, systemizer
2) Systemize RGC (Oreo requires it to be systemized as a priv-app)
3) Start VNC as noted above, start RGC

# WE DO NOT GUARANTEE FOR THE ENTIRE THING TO BE RUNNING PERFECTLY FINE

### Todos

 - Write tests
 - Write VNC app
 - Improve scans
 - Improve errorhandling
 - Support more/all resolutions

# Discord
For minor help, reporting resolutions (instructions on how to do so will be given sometime in the future), bugreports
[Join the discord server](https://discord.gg/MC3vAH9)


License
----

GNU GPL
