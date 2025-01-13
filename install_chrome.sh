#!/bin/bash

set -e  # Exit on error

echo "Installing Chrome dependencies..."
sudo apt-get update
sudo apt-get install -y wget gnupg

echo "Adding Google Chrome repository..."
wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
sudo sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'

echo "Installing Google Chrome..."
sudo apt-get update
sudo apt-get install -y google-chrome-stable

echo "Verifying installation..."
if google-chrome --version; then
    echo "Chrome installed successfully"
    exit 0
else
    echo "Chrome installation failed"
    exit 1
fi
