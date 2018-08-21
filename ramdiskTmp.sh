#/bin/bash

#TODO: ask user if he REALLY wants to run the following commands

rm -rf ../temp_mad
mkdir ../temp_mad
sudo mount -t tmpfs -o size=200M none ../temp_mad
