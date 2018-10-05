Limitations
===========

.. contents:: :local:

Details
-------

* The only supported aspect ratio is 16:9. If you have a softkey bar, disable it for PoGO.
    * To do this for phones without the option run the following in a terminal on the phone
        `settings put global policy_control immersive.navigation=*`
    * You can do this using `adb shell` commands.
* It takes time to load when you teleport between different locations. So faster phones may handle the loading better. We are testing on low end specs like `Redmi 5A <https://www.mi.com/in/redmi-5a/>`_ for $75. A parameter to adjust the delays in between teleports and screenshots will most likely be added.
* Sometimes the Raids won't get reported to the DB and we are in the process of debugging it. A potential help is removing the files inside the hash-folder.
* RemoteGPSController (RGC) is know to sometimes crash follow the below options:
    * Disable Battery Optimization in Settings-> Apps -> RGC -> Battery
    * Go to RGC-Settings (within RGC) and enable OOM Overwrite
