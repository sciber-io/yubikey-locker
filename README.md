
# YubiKey Autolocker by Sciber

To enable automatic lock when removing the YubiKey.

:warning:
Avoid running this tool without a YubiKey present as it will then lock your computer.

### Comandline options (Linux and MAC)
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

### Windows
1. Download the installer sciber-yklocker.msi from [releases](https://github.com/sciber-io/yklocker/releases)
2. Run the installer (installs the service SciberYklocker for you)
3. Follow Jonas guide on his blog: https://swjm.blog/locking-the-workstation-on-fido2-security-key-removal-part-2-80962c944c78 to set up GPO/Intune control to decide what you want to do if the YubiKey is removed.

```bash
# Instead of changing the program's behavior via the commandline its done via the registry.
# removalOptions: Lock,Logout,doNothing
# timout: a number
HKEY_LOCAL_MACHINE\SOFTWARE\Policies\Yubico\YubiKey Removal Behavior
  - removalOption Lock
  - timeout 10
```

### Linux
Download sciber-yklocker.linux and execute it in a terminal (requires you to keep that terminal window open).

### Mac
Download sciber-yklocker.darwin and execute it in a terminal (requires you to keep that terminal window open).
- Only supports lockout



### Credits
####  [Jonas Markström](https://github.com/JMarkstrom/YubiKey-Removal-Behavior)
Thank you for letting us reuse your AD/Intune templates to enable control via GPO's. Also thank you for the inspiration and discussions we have.
- https://github.com/JMarkstrom/YubiKey-Removal-Behavior
- https://swjm.blog/locking-the-workstation-on-fido2-security-key-removal-part-2-80962c944c78


### Development

See [README-development.md](README-development.md)
