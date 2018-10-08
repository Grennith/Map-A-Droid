Database Setup
==============

.. contents:: :local:

Prerequisites
-------------
You will need a MySQL server installed:

* (Tutorial from RocketMap) `Installing MySQL <https://rocketmap.readthedocs.io/en/develop/basic-install/mysql.html>`_

A new table, called ``trshash`` will be created at the first run. You can create it manually using the following query:

.. code-block:: sql

    CREATE TABLE if not exists trshash (
    hashid MEDIUMINT NOT NULL AUTO_INCREMENT,
    hash VARCHAR(255) NOT NULL,
    type VARCHAR(10) NOT NULL,
    id VARCHAR(255) NOT NULL,
    count INT(10) NOT NULL DEFAULT 1,
    modify DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (hashid));


Remember: The account you use for Map-A-Droid has to have CREATE/DROP permissions as well as
INSERT, UPDATE, DELETE, and SELECT!
