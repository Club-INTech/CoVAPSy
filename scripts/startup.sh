#!/bin/bash

# Specify the PATH
export PATH=/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin

# Change to the project directory
cd /home/intech/CoVAPSy

# Pull the latest changes from the repository
git pull 

# Create the test directory
mkdir -p /home/intech/CoVAPSy/test

# Run the main Python script
python /home/intech/CoVAPSy/src/HL/main.py