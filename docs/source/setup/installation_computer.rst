Computer Setup
==============

.. contents:: :local:

Prerequisites
-------------
Install `Python 2.7` according to docs for your platform.

Once Python is installed, ensure that `pip` and `Python` is installed correctly by running:
* `python --version` - should return `2.7.X`
* `pip --version` - If it returns a version, it is working. If not, `visit here <https://packaging.python.org/tutorials/installing-packages/#ensure-you-can-run-pip-from-the-command-line>`_

Clone this repository:

.. code-block:: bash

    git clone https://github.com/Grennith/Map-A-Droid.git

Make sure you're in the directory of Map-A-Droid and run:

.. code-block:: bash

    pip install -r requirements.txt

Mac
---
Run the shell from `here <https://github.com/milq/milq/blob/master/scripts/bash/install-opencv.sh>`_

> If face issues with the shell script ensure that Open JDK has installed correctly and try and running lines 57-70 individually and on line 67 run just `cmake` without the parameters.

.. code-block:: bash

    brew install imagemagick
    brew install tesseract --all-languages


Linux
-----
Ubuntu/Debian, run `apt install tesseract-ocr python-opencv`

If you do not get OpenCV 3.0 or above:
Run the shell from `here <https://github.com/milq/milq/blob/master/scripts/bash/install-opencv.sh>`_

> If face issues with the shell script ensure that Open JDK has installed correctly and try and running lines 57-70 individually and on line 67 run just `cmake` without the parameters.

All other parts are installed from the requirements.txt


Raspberry Pi
------------

.. code-block:: bash

    // TODO - there is a setup script in this repo though!

Docker
------------

.. code-block:: bash

    // TODO - there is a dockerfile but no instructions here...

Windows
-------

.. code-block:: bash

    // TODO