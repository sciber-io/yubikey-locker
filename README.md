
# YubiKey Autolocker by Sciber

To enable automatic lock when removing the YubiKey.

### Comandline options (ALL OS's)
```bash
# Defaults to LOCKOUT, can be set to LOGOUT with
sciber-yklocker.exe -l logout

# Defaults to checking for a yubikey every 10 seconds, can be changed with
sciber-yklocker.exe -t 20
```

### Windows
1. Download the installer sciber-yklocker.msi from [releases](https://github.com/sciber-io/yklocker/releases)
2. Run the installer (installs the service SciberYklocker for you)
3. Follow Jonas guide on his blog: https://swjm.blog/locking-the-workstation-on-fido2-security-key-removal-part-2-80962c944c78 to set up GPO/Intune control to decide what you want to do if the YubiKey is removed.

```bash
# Change behavior on Windows via the registry:
# removalOptions: lock,logout
HKEY_LOCAL_MACHINE\SOFTWARE\Policies\Yubico\YubiKey Removal Behavior
  - removalOption lock
  - timeout 10
```

### Linux
Download sciber-yklocker.linux and execute it in a terminal (requires you to keep that terminal window open).

### Mac
Download sciber-yklocker.darwin and execute it in a terminal (requires you to keep that terminal window open).
- Only supports lockout

### Warning
Avoid running this tool without a YubiKey present as it will then lock your computer.

### Credits
####  [Jonas Markström](https://github.com/JMarkstrom/YubiKey-Removal-Behavior)
Thank you for letting us reuse your AD/Intune templates to enable control via GPO's. Also thank you for the inspiration and discussions we have.
- https://github.com/JMarkstrom/YubiKey-Removal-Behavior
- https://swjm.blog/locking-the-workstation-on-fido2-security-key-removal-part-2-80962c944c78


### Development
```
# Install tox
python3.11 -m pip install --user tox

# Run tests
python3.11 -m tox

# Run linting
python3.11 -m tox -e lint

# Build binary
python3.11 -m tox -e build -- sciber-yklocker.exe

```
In case something is unclear - you should be able to follow the process in ci.yml
