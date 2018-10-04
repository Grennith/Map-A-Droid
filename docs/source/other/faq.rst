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


