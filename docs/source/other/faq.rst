FAQ
=====================================

.. contents:: Table of Contents
   :depth: 2
   :local:


General
-------------------------------------

Where should I go for support?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If, after *carefully* reading the Wiki and the rest of this FAQ, you can visit
our `Discord <https://discord.gg/MC3vAH9>`_.

For bugs or support requests, feel free to also open an issue on our
`GitHub <https://github.com/Grennith/Map-A-Droid/issues>`_ - just make sure
to use the correct template and to fill out all the information!


Gyms
--------------------------------------

How to add/edit gyms?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
- Add the gym name, coords and the link to the image to the `updateGyms.txt`. Examples for the correct syntax can be found in the file
- Call `python updateGyms.py` to add/update gyms in your DB
- Call `python downloadGymImages.py` to download gym images with the correct name
- Call `python downloadCoords.py` to update the `coords.csv` file with newly added gyms

Rooting Issues/Magisk
--------------------------------------

Cant login to PoGo - device incompatible etc?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
0. Assume you have installed Magisk
1. Make sure that you have repackaged Magisk so that the package name is jumbled. `Settings > General > Repackage`
2. Make sure that Magisk is hide in settings of the app `Settings > Magisk > Toggle Magisk Hide`
3. Ensure that Pokemon Go is specifically hidden too in the menu `Magisk Hide > select Pokemon GO`
4. Ensure that all files from flashing the ROM and also folders with Magisk references are deleted
5. Clear app cache before trying again.

Using Raid information
--------------------------------------

How do i get the raids on a map?
````````````````````````````````````````````
We would recommend either the front end of Rocket Map - this has been forked to use OSM rather than Google Maps Api. If you prefer you can use PMSF we recommend WhiteWillem's fork

`Forked Rocket Map <hhttps://github.com/cecpk/RocketMap>`_

`WhiteWillem PMSF <https://github.com/whitewillem/pmsf>`_

How do i get it to output to Telegram or Discord?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
So much like in the 'old days' we support the standard set out in `PokeAlarm <https://github.com/Pokealarm/pokealarm>`_

Their wiki is `here <https://pa.readthedocs.io/en/master/index.html>`_

You will need to setup the webhook parameter in the config.ini in the same way you used to with RocketMap or Monocle with IP and Ports etc.

