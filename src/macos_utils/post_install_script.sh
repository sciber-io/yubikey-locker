#!/bin/sh
# Unload existing module
logger "Unloading any existing module of Sciber YubiKey Locker"
launchctl unload -w /Library/LaunchAgents/io.sciber.yubikeylocker.plist
logger "Starting Sciber YubiKey Locker post-install-scripts"
# log show --process logger --debug --last 24h
# log show --predicate 'eventMessage contains "sciber"' --info --last 2h
touch "/Library/LaunchAgents/io.sciber.yubikeylocker.plist"
if [ $? != 0 ]; then
    logger "yubikey-locker: Something went wrong with touch plist"
fi
cat > /Library/LaunchAgents/io.sciber.yubikeylocker.plist <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">

<!--
File location: /Library/LaunchAgents/io.sciber.yubikeylocker.plist
-->


<dict>
    <key>Label</key>
    <string>io.sciber.yubikeylocker</string>

    <!-- Will start when user logs in -->
    <key>RunAtLoad</key>
    <true/>

    <key>ProgramArguments</key>
    <array>
        <string>/Applications/yubikey-locker-macos.app/Contents/MacOS/yubikey-locker-macos</string>
        <!-- Add arguments if you want to change app behavior-->
        <string>-l</string>
        <string>Lock</string>
        <string>-t</string>
        <string>10</string>
    </array>

    <!-- Tell launchd that this program should be running at all times -->
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
EOF
if [ $? != 0 ]; then
    logger "Sciber YubiKey Locker: Something went wrong with cat to plist"
fi
logger "Starting service Sciber YubiKey Locker"
launchctl load -w /Library/LaunchAgents/io.sciber.yubikeylocker.plist
logger "Finished Sciber YubiKey Locker post-install-scripts"
