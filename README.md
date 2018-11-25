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
* It takes time to load when you teleport between different locations. So faster phones may handle the loading better. We are testing on low end specs like [Redmi 5A](https://www.mi.com/in/redmi-5a/) for $75. A parameter to adjust the delays in between teleports and screenshots is presented. Check the help of startWalker.py
* OCR won't be 100% correct, you can use MADmin to correct any faulty scans.
* RemoteGPSController (RGC) is know to sometimes crash follow the below options:
  * Disable Battery Optimization in Settings-> Apps -> RGC -> Battery
  * Go to RGC-Settings (within RGC) and enable OOM Overwrite

## Some (but not limiting) examples of phones working with the project:
* Redmi 5A (annoying to setup) running LineageOS 15.1
* Samsung S5(+) running LineageOS 15.1
* Motorola G4 running LineageOS 15.1
* HTC One M7 running LineageOS 14.1
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

> If face issues with the shell script ensure that Open JDK has installed correctly and try and running lines 57-70 individually and on line 67 run just `cmake` without the parameters.

All other parts are installed from the requirements.txt

#### MacOS (Using Brew ([How to Install Brew](https://brew.sh/)))
Run the shell from [here](https://github.com/milq/milq/blob/master/scripts/bash/install-opencv.sh)

> If face issues with the shell script ensure that Open JDK has installed correctly and try and running lines 57-70 individually and on line 67 run just `cmake` without the parameters.

```bash
brew install imagemagick
brew install tesseract --all-languages
```

#### Windows (Tested on Windows 10 x64)
```bash
Install Python 3.6 
https://www.python.org/ftp/python/3.6.0/python-3.6.0-amd64.exe
Make sure to add Python to PATH during the setup.

Git  Windows:
https://git-for-windows.github.io/

Microsoft Visual C++ Compiler  Python 3.6
https://wiki.python.org/moin/WindowsCompilers

Node.js  Windows
https://nodejs.org/en/download

Tesseract
https://github.com/UB-Mannheim/tesseract/wiki 

x32b: https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w32-setup-v4.0.0-rc4.20181024.exe
x64b: https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w64-setup-v4.0.0-rc4.20181024.exe

Clone this repository:
git clone https://github.com/Grennith/Map-A-Droid.git

Make sure you are on the directory of Map-A-Droid and run:
pip install -r requirements.txt
Fix error about twisted error:
https://www.lfd.uci.edu/~gohlke/pythonlibs/#twisted
https://download.lfd.uci.edu/pythonlibs/h2ufg7oq/Twisted-18.9.0-cp37-cp37m-win_amd64.whl
I'd recommend saving that wheel file in the directory where you've installed Python i.e somewhere in Local Disk C
Then visit the folder where the wheel file exists and run pip install Twisted18.9.0-cp37-cp37m-win_amd64.whl
pip install setuptools
python3 -m pip install -U pip setuptools
Run pip install -r requirements.txt


Fix error about opencv "No matching distribution found for opencv-python (from -r requirements.txt )"
pip install --upgrade pip
pip install opencv-python
pip install opencv-contrib-python
pip install opencv-python-headless
pip install tesseract-ocr python-opencv
pip install -r requirements.txt

Dont forget to restart your pc  and enjoy :)

```
### Prerequisites - Mobile
1. Ensure your phone has an unlocked bootloader and it able to support root. Lineage OS is a good place to start for a custom ROM and they have good installation instruction for each device.
2. Install [Magisk](https://forum.xda-developers.com/apps/magisk/official-magisk-v7-universal-systemless-t3473445)

3. Install [RemoteGPSController (RGC)](https://www.github.com/Grennith/Map-A-Droid/blob/master/APKs/RemoteGpsController.apk) located in the `APKs` github folder.

4. Install [Link2SD](https://play.google.com/store/apps/details?id=com.buak.Link2SD&hl=en_GB) and ensure that RemoteGPSController is converted to a system app.

5. To help with rubberbanding when teleporting do the following
    *  Disable **background** data of Google Play Services
    *  Check the GMS option within RGC settings

### MySQL - Database
You will need a MySQL server installed:
* (Tutorial from RocketMap) [Installing MySQL](https://rocketmap.readthedocs.io/en/develop/basic-install/mysql.html)

Remember: The account you use for Map-A-Droid has to have CREATE/DROP permissions as well as
INSERT, UPDATE, DELETE, and SELECT!

### Configuration
1. Rename `config.ini.example` to `config.ini` and fill out:
    - MySQL Settings (RM or Moncole Database)
    - Device Specifics (Width and Height resolutions in pixels)
    - Path Settings (like pogo assets)
    - Timezone Settings (if you use RM)
    - Coords CSV (Create a blank "coords.csv" file and set `file: coords.csv`)

</br>

2) We need gym images and there are two solutions:
    - If you have a RocketMap/Monocle database with old gym-details, run `downloadGymImages.py`
    - Or, grab the images from [Ingress Intel Map](https://www.ingress.com/intel)

(The images should be located in `gym_img` folder)

</br>

3) We also need gym locations and there are two solutions:
    - If you have a RocketMap/Monocle database with old gym-details, run `downloadCoords.py`
    - Or, grab the locations from [Ingress Intel Map](https://www.ingress.com/intel)

(The coords should be located in `coords.csv` if you followed the last step in 1.)

</br>

4) Fill out the rest of the `config.ini`, the important parts are:
    - Telnet Settings (RemoteGpsController)

### Running
1. Mobile - Start Remote GPS Controller.
    * Select Start within the app to start GPS
    * Select MediaProjection to allow touch commands
</br>

2. PC - Make sure you're in the directory of Map-A-Droid and run the following two commands

To start the GPS walking around
`python startWalker.py -os`

To start the processing of the screenshot that have been taken
`python startWalker.py -oo`

Best practice is to run both commands in seperate [screen](https://www.gnu.org/software/screen/) sessions.

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
