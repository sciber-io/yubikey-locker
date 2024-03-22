
# Development
> [!IMPORTANT]  
> Requirements: Python3.11+  
> Since we use yubikey-manager for checking if a YubiKey is present we get dependencies from that to Windows, Linux, Mac: https://developers.yubico.com/yubikey-manager/Development.html  
>   



The automated test and buildflow in used for the GitHub builds can be seen in [.github/workflows/ci.yml](.github/workflows/ci.yml)
For example: 
- How tox is used to install requirements and build executables
- How the Windows MSI executable is built


____

After changing code make sure to run tests, and then build your excecutable:
```
# Run in virtual environment
python3-11 -m venv .venv

# Activate virtual environment
## Windows
.venv/Scripts/activate.ps1

## other
source .venv/bin/activate

# Install tox
python3.11 -m pip install tox

# Install sciber_yklocker package in edit mode
pip install -e .

# Install requirements and run tests
python3.11 -m tox

# Run linting
python3.11 -m tox -e lint

# Build binary
python3.11 -m tox -e build_win|build_linux|build_macos

## Binaries will be placd in ./build/

```

### Intune version of app:
This needs to be increased for Intune to roll out a new version of the app.
- Version number is changed in [src/macos_utils/sciber-yklocker-macos.spec](src/macos_utils/sciber-yklocker-macos.spec)
- Version number is changed in [src\windows_utils\sciber-yklocker.wxs](src\windows_utils\sciber-yklocker.wxs)

### Linux prerequisites
Necessary to install a few packages:
```sudo apt install -y libpcsclite-dev python3.11-dev swig pcscd```


### Windows install service

In case you do want to skip the MSI:
```
sc.exe create SciberYkLocker binPath="C:\Program Files\Sciber\sciber-yklocker\sciber-yklocker.exe" start=auto
sc.exe start SciberYkLocker```
