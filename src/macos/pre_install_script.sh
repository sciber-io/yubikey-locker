#!/bin/sh
# Our application should be installed at /Applications/sciber-yklocker-macos.app
# If a new version is released and the path is occupied by an older version Intune installs it
# in a new subdirectory /Applications/sciber-yklocker-macos/sciber-yklocker-macos.app

# Remove autostart config
rm /Library/LaunchAgents/io.sciber.sciberyklocker.plist

# Kill current processes
kill -9 $(ps aux | grep sciber-yklocker | grep -v grep | awk '{print $2}')

# Remove old application
rm -rf /Applications/sciber-yklocker-macos.app
