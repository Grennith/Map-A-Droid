# Map'A'Droid
![Python 2.7](https://img.shields.io/badge/python-2.7-blue.svg)  

![MAD-Banner](examples/banner_small_web.png)

The Raid Mapper is a Raid scanner for Pokemon GO, based on Android devices and OCR.  

<img src="https://raw.githubusercontent.com/Grennith/Map-A-Droid/master/examples/example_map.PNG" width="500" height="500">

## Information
*  [Discord](https://discord.gg/MC3vAH9) - For general support  
*  [Github Issues](https://github.com/Grennith/Map-A-Droid/issues) - For reporting bugs (not for support!)  

## Requirements  
* [PogoAssets](https://github.com/ZeChrales/PogoAssets)  
* Google or PTC account with minimum level 5 and no Raid-bosses in the dex  
* Mobile with Android 6 or higher
* Root privileges [Magisk](https://forum.xda-developers.com/apps/magisk/official-magisk-v7-universal-systemless-t3473445) 
* [Remote GPS Controller](https://github.com/Grennith/Map-A-Droid/blob/master/APKs/RemoteGpsController.apk)  

## Current limitations
* The only supported aspect ratio is 16:9. If you have a softkey bar, disable it for PoGO.  
  * To do this for phones without the option run the following in a terminal on the phone
    `settings put global policy_control immersive.navigation=*`
  * You can do this using `adb shell` commands.
* It takes time to load when you teleport between different locations. So faster phones may handle the loading better. We are testing on low end specs like [Redmi 5A](https://www.mi.com/in/redmi-5a/) for $75. A parameter to adjust the delays in between teleports and screenshots will most likely be added.   
* Sometimes the Raids won't get reported to the DB and we are in the process of debugging it. A potential help is removing the files inside the hash-folder.  
* RemoteGPSController (RGC) is know to sometimes crash follow the below options:
  * Disable Battery Optimization in Settings-> Apps -> RGC -> Battery
  * Go to RGC-Settings (within RGC) and enable OOM Overwrite

## Some (but not limiting) examples of phones working with the project:
* Redmi 5A (annoying to setup) running LineageOS 15.1
* Samsung S5(+) running LOS 15.1
* Motorola G4 running LineageOS 15.1
* HTC One M7 running LOS 14.1
* Samsung XCover 4 running stock Android 7.1.2

## Installation
### Prerequisites - Computer
Install `Python 2.7` according to docs for your platform.  

Once Python is installed, ensure that `pip` and `Python` is installed correctly by running:  
* `python --version` - should return `2.7.X`  
* `pip --version` - If it returns a version, it is working. If not, [visit here](https://packaging.python.org/tutorials/installing-packages/#ensure-you-can-run-pip-from-the-command-line)  

Clone this repository:  
`git clone https://github.com/Grennith/Map-A-Droid.git`  

Make sure you're in the directory of Map-A-Droid and run:  
`pip install -r requirements.txt`

*Depending on your OS, you may need to install the following:*
#### Ubuntu/Debian
Ubuntu/Debian, run `apt install tesseract-ocr python-opencv`

If you do not get OpenCV 3.0 or above:
Run the shell from [here](https://github.com/milq/milq/blob/master/scripts/bash/install-opencv.sh)

> If face issues with the shell sceript ensure that Open JDK has installed correctly and try and running lines 57-70 individually and on line 67 run just `cmake` without the paramters.

All other parts are installed from the requirements.txt

#### MacOS (Using Brew ([How to Install Brew](https://brew.sh/)))
Run the shell from [here](https://github.com/milq/milq/blob/master/scripts/bash/install-opencv.sh)

> If face issues with the shell sceript ensure that Open JDK has installed correctly and try and running lines 57-70 individually and on line 67 run just `cmake` without the paramters.

```bash
brew install imagemagick
brew install tesseract --all-languages
```
 
#### Windows
```bash
// TODO
```
### Prerequisites - Mobile
1. Ensure your phone has an unlocked bootloader and it able to support root. Lineage OS is a good place to start for a custom ROM and they have good installation instruction for each device.
2. Install [Magisk](https://forum.xda-developers.com/apps/magisk/official-magisk-v7-universal-systemless-t3473445) by flashing ([App Installs/ROM Feature Installs via Flashing](https://forum.xda-developers.com/wiki/Flashing_Guide_-_Android)).  

3. Install RemoteGPSController (RGC) [here](http://www.github.com/Grennith/Map-A-Droid/blob/master/APKs/RemoteGpsController.apk) located in the `APKs` github folder.

4. Install [Link2SD](https://play.google.com/store/apps/details?id=com.buak.Link2SD&hl=en_GB) and ensure that RemoteGPSController is converted to a System Apps.

5. To help with rubberbanding when teleporting do the following
    *  Disable **background** data of Google Play Services
    *  Check the GMS option within RGC settings


### MySQL - Database  
You will need a MySQL server installed:  
* (Tutorial from RocketMap) [Installing MySQL](https://rocketmap.readthedocs.io/en/develop/basic-install/mysql.html) 

You will also need to create the `trshash` table using the following query
```sql
Create table if not exists trshash ( 
hashid MEDIUMINT NOT NULL AUTO_INCREMENT,
hash VARCHAR(255) NOT NULL,
type VARCHAR(10) NOT NULL,
id VARCHAR(255) NOT NULL,
count INT(10) NOT NULL DEFAULT 1,
PRIMARY KEY (hashid));
```

Remember: The account you use for Map-A-Droid has to have CREATE/DROP permissions as well as 
INSERT, UPDATE, DELETE, and SELECT!

### Configuration
1. Rename `config.ini.example` to `config.ini` and fill out:
    - Screen Method (Set it to 0)
    - MySQL Settings (RM or Moncole Database)  
    - Device Specifics (Width and Height resolutions in pixels)
    - Path Settings (pogoasset only)  
    - Timezone Settings  
    - Coords CSV (Create a blank "coords.csv" file and set `file: coords.csv`)  

</br>

2) We need gym images and there are two solutions:  
    - If you have a RocketMap/Monocle database with old gym-details, run `downloadfortimg.py`  
    - Or, grab the images from [Ingress Intel Map](https://www.ingress.com/intel)  

(The images should be located in `gym_img` folder)

</br> 

3) We also need gym locations and there are two solutions:
    - If you have a RocketMap/Monocle database with old gym-details, run `downloadDBCords.py`  
    - Or, grab the locations from [Ingress Intel Map](https://www.ingress.com/intel)  

(The coords should be located in `coords.csv` if you followed the last step in 1.)

</br>

4) Fill out the rest of the `config.ini`, the important parts are:  
    - Telnet Settings (RemoteGpsController)

### Running
1. Mobile - Start Remote GPS Controller.
    * Select Start within the app to start GPS
    * Select MediaProjection to allow touch commands  
    * 
</br>

4. PC - Make sure you're in the directory of Map-A-Droid and run the following 2 commands 

To start the GPS walking around
`python startWalker.py -os`

To start the processing of the screenshot that have been taken
`python startWalker.py -oo`


>Note if running via ssh you may face issues around "no screen available" to get around the prefix your commands with `MPLBACKEND=Agg`

<br>

## Updating the application
Make sure you're in the directory of Map-A-Droid and run:  
```
git pull
pip install -r requirements.txt 
```
>If there are changes to OCR that require OCR hashing to be cleared it will likely be announced in Discord. But the argument you add to your `-oo` command is `-chd`
The command will look like this:
`python startWalker.py -oo -chd`

**WE DO NOT GUARANTEE IT WILL BE RUNNING PERFECTLY FINE, AS THE PROJECT IS IN ONGOING DEVELOPMENT**

## TODO
* Write tests  
* Improve scans  
* Improve error handling  
* Support more/all resolutions  

License
----

See [LICENSE - GNU GENERAL PUBLIC LICENSE](https://github.com/Grennith/Map-A-Droid/blob/master/LICENSE).
