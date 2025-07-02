#!/bin/bash

# Update package list
sudo apt-get update

# Install Python3 and pip
sudo apt-get install -y python3 python3-pip

# Install required Python packages
pip3 install -r ../requirements.txt

# Install additional dependencies for camera and motor control
sudo apt-get install -y python3-opencv
sudo apt-get install -y python3-rpi.gpio

# Clean up
sudo apt-get autoremove -y
sudo apt-get clean