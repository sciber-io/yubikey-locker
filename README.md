# Sciber YubiKey Locker
[![main - tests and build](https://github.com/sciber-io/yklocker/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/sciber-io/yklocker/actions/workflows/ci.yml)

For YubiKey users to enable automatic device locking when removing the YubiKey.

<img src="images/sciber_yklocker.png" alt="YubiKey Autolocker by Sciber" width="250"/>




### Possible action to take when a YubiKey is not found
| Action        | Windows   | Mac  | Linux (Ubuntu)  |
| ---           | ---       | ---  | ---    |
| Nothing       | ✅       | ✅   | ✅    |
| Lock Computer | ✅       | ✅   | ✅    |
| Log Out User  | ✅       | ✅   | ✅    |

### Available installation instructions
| Method        | Windows   | Mac   | Linux (Ubuntu) |
| ---           | ---       | ---  | ---    |
| Intune        | ✅       | ✅   | ❌
| Manual        | ✅       | ✅   | ✅    |

### How to inspect application logs:
Windows: ```Get-EventLog -LogName Application -Source SciberYklocker | Select TimeGenerated,ReplacementStrings ```  
Mac:   ```log show --predicate 'process = "sciber-yklocker-macos"' ```  
Linux (Ubuntu):  ```cat /var/log/syslog | grep sciber-yklocker ```  


## Installation via Intune
### Windows
1. Download the .admx and .adml files from the `src/windows_utils/Administrative template` folder
2. Intune/GPO: Follow Jonas guide on his blog: https://swjm.blog/locking-the-workstation-on-fido2-security-key-removal-part-2-80962c944c78 to set up GPO/Intune control to decide what you want to do if the YubiKey is removed.
### Mac
1. Add an macOS app, upload sciber-yklocker-macos.pkg
2. Add the contents of `src/macos_utils/post_install_script.sh` to the post-install-script box in Intune
3. Depending on the groups that the app is pushed to, change contents of the post-install-script to pass apropriate arguments to the application


## Manual Installation
### Windows
1. Download and execute sciber-yklocker.msi from [releases](https://github.com/sciber-io/yklocker/releases)
#### Set registry values

1. Download the .admx and .adml files from the `src/windows_utils/Administrative template` to `C:\Windows\PolicyDefinitions`
2. Start "local group policy editor" and navigate to:
  - "Computer Configuration"
    - "Administrative Templates"
      - "Sciber Yklocker Settings"
        - Turn on to set registry values

### Mac
1. Download and execute sciber-yklocker-macos.pkg from [releases](https://github.com/sciber-io/yklocker/releases)
2. Download, modify script content if necessary, and execute `src/macos_utils/post_install_script.sh`
3. Perform a logout or a reboot

### Linux (Ubuntu)
1. Download sciber-yklocker-linux from [releases](https://github.com/sciber-io/yklocker/releases) into  `/home/<your-user>/.sciber/sciber-yklocker-linux `
2. Download [the service file](https://github.com/sciber-io/yklocker/blob/main/src/linux_utils/sciber-yklocker.service) to `/etc/systemd/user/yklocker.service`
3. Modify the service file to specify the correct path to the binary
4. Enable the service to start on reboot:  ```systemctl enable yklocker --user ```
5. Start the service:  ```systemctl start yklocker --user ```



## Default behavior
sciber-yklocker will check if there is a YubiKey present every 10 seconds. If no command-line arguments / registry values instruments the application to lock the computer it will do nothing.






### Comand line options for Linux/MacOS
```bash
# Run sciber-yklocker
# Defaults to doNothing with the device after 10 seconds without a YubiKey
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
Special thanks to [Jonas Markström](https://github.com/JMarkstrom/) for valuable feedback and support during this project.


## Known Issues
[MacOS: The check for the Yubikey may cause issues with gpg](https://github.com/sciber-io/yklocker/issues/78)
____
For information regarding how to continue development and build your own binaries see [README-development.md](README-development.md)
