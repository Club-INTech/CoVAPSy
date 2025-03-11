#!/bin/bash

# Specify the PATH
export PATH=/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin

# Wait until WiFi is acquired
while ! ping -c 1 google.com &> /dev/null; do
    echo "Waiting for WiFi connection..."
    sleep 5
done

# Change to the project directory
cd /home/intech/CoVAPSy

# Pull the latest changes from the repository
git pull >> /home/intech/CoVAPSy/git_pull.log 2>&1

# Run the main Python script
python /home/intech/CoVAPSy/src/HL/main.py >> /home/intech/CoVAPSy/main.log 2>&1