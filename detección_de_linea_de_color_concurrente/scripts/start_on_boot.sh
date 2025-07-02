#!/bin/bash

# This script sets up the Raspberry Pi car project to start automatically on boot.

# Navigate to the project directory
cd /path/to/your/raspberry-pi-car

# Run the main Python script
python3 src/main.py &

# Exit the script
exit 0