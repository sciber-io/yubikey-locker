#!/bin/sh
# Our application should be installed at /Applications/yubikey-locker-macos.app
# If a new version is released and the path is occupied by an older version Intune installs it
# in a new subdirectory /Applications/yubikey-locker-macos/yubikey-locker-macos.app

# Maybe just the changed identifer that caused this


# Remove autostart config
plistPath = "/Library/LaunchAgents/io.sciber.yubikeylocker.plist"
if [ -f $plistPath ]; then
  rm $plistPath
fi
# Kill current processes
kill -9 $(ps aux | grep yubikey-locker | grep -v grep | awk '{print $2}')

# Remove old application
rm -rf /Applications/yubikey-locker-macos.app
