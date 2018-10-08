OCR
======

OCR is the code that will processes the images that the walker has captures and places in the ``screenshots`` folder. From where it will find a match with the images that are in ``gym_images`` and from there insert into your database and also send a webhook if appropriate
The route it walks is visible in MADmin.

To start the walker it is ``python startWalker.py -os``