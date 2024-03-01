#!/bin/sh
# Unload existing module
logger "Unloading any existing module of sciber yklocker"
launchctl unload -w /Library/LaunchAgents/io.sciber.sciberyklocker.plist
logger "Starting sciber-yklocker post-install-scripts"
# log show --process logger --debug --last 24h
# log show --predicate 'eventMessage contains "sciber"' --info --last 2h
touch "/Library/LaunchAgents/io.sciber.sciberyklocker.plist"
if [ $? != 0 ]; then
    logger "sciber-yklocker: Something went wrong with touch plist"
fi
cat > /Library/LaunchAgents/io.sciber.sciberyklocker.plist <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">

<!--
File location: /Library/LaunchAgents/io.sciber.sciberyklocker.plist
-->


<dict>
    <key>Label</key>
    <string>io.sciber.sciberyklocker</string>

    <!-- Will start when user logs in -->
    <key>RunAtLoad</key>
    <true/>

    <key>ProgramArguments</key>
    <array>
        <string>/Applications/sciber-yklocker-macos.app/Contents/MacOS/sciber-yklocker-macos</string>
        <!-- Add arguments if you want to change app behavior-->
        <string>-l Lock -t 10</string>
    </array>

    <!-- Tell launchd that this program should be running at all times -->
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
EOF
if [ $? != 0 ]; then
    logger "sciber-yklocker: Something went wrong with cat to plist"
fi
logger "Starting service sciber-yklocker"
launchctl load -w /Library/LaunchAgents/io.sciber.sciberyklocker.plist
logger "Finished sciber-yklocker post-install-scripts"
