
# YubiKey Autolocker by Sciber
Requirements: Python3.11+

### Development
```
# Install tox
python3.11 -m pip install --user tox

# Run tests
python3.11 -m tox

# Run linting
python3.11 -m tox -e lint

# Build binary
python3.11 -m tox -e build_win

```
In case something is unclear - you should be able to follow the process in ci.yml


### MacOS
Version number is changed in src/macos/sciber-yklocker-macos.spec
This needs to be increased for Intune to roll out a new version of the app.


### Other
Pyinstaller cmd:
pyinstaller --clean -F -n "sciber-yklocker" "..\src\sciber_yklocker.py"

In case you do not want to skip the MSI:

sc.exe create SciberYkLocker binPath="C:\Program Files\Sciber\sciber-yklocker\sciber-yklocker.exe" start=auto
sc.exe start SciberYkLocker
