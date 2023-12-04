# YubiKey Autolocker by Sciber
[![main - tests and build](https://github.com/sciber-io/yklocker/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/sciber-io/yklocker/actions/workflows/ci.yml)

For YubiKey users to enable automatic device locking when removing the YubiKey.

<img src="src/sciber_yklocker.png" alt="YubiKey Autolocker by Sciber" width="250"/>


:warning: Avoid running this tool without a YubiKey present as it will then lock your computer.

### Default behavior
sciber-yklocker will check if htere is a YubiKey present every 10 seconds, and if there is not the computer will be locked.

On Windows this will only happen if the proper register values are set - otherwise it defaults to doNothing.

## Installation
### Windows
1. Download the installer sciber-yklocker.msi from [releases](https://github.com/sciber-io/yklocker/releases)
2. Run the installer (installs the service SciberYklocker for you)
#### Set registry values
1. Download the .admx and .adml files from the "Administrative template" folder
2. Intune/GPO: Follow Jonas guide on his blog: https://swjm.blog/locking-the-workstation-on-fido2-security-key-removal-part-2-80962c944c78 to set up GPO/Intune control to decide what you want to do if the YubiKey is removed.
3. (Locally: download the amdx and adml file to your computer and place them in C:\Windows\PolicyDefinitions, then start local group policy editor -> Computer Configuration -> Administrative Templates -> Sciber Yklocker Settings --> turn on to get registry values)


### Linux
Download sciber-yklocker-linux and execute it in a terminal (requires you to keep that terminal window open).



### Mac
- Does not support Logout

Download sciber-yklocker-macos and execute it in a terminal (requires you to keep that terminal window open).

#### No terminal
1. Download sciber-yklocker-macos and io.sciberyklocker.plist to (and then restart computer)
- /Applications/sciber-yklocker-macos
- /Library/LaunchAgents/io.sciber.sciberyklocker.plist
2. Application output is written to /Applications/sciber-yklocker-macos.log and /Applications/sciber-yklocker-macos-error.log



### Comandline options (Linux and Mac)
```bash
# Run sciber-yklocker
# Defaults to locking the device after 10 seconds without a YubiKey
sciber-yklocker

# Optional arguments:
# Set removalOption
-l Lock|Logout|doNothing

# Set timeout
-t 20

# Example
sciber-yklocker -l Logout -t 30
```


### Credits
####  [Jonas Markström](https://github.com/JMarkstrom/YubiKey-Removal-Behavior)
Thank you for letting us reuse your AD/Intune templates to enable control via GPO's. Also thank you for the inspiration and discussions we have.
- https://github.com/JMarkstrom/YubiKey-Removal-Behavior
- https://swjm.blog/locking-the-workstation-on-fido2-security-key-removal-part-2-80962c944c78


### Development
To change behavior and compile your own executables see [README-development.md](README-development.md)
