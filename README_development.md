
# Development
> [!IMPORTANT]
> Built with: Python3.13
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
python -m venv .venv

# Activate virtual environment
## Windows
.venv/Scripts/activate.ps1

## other
source .venv/bin/activate

# Install tox
python -m pip install tox

# Install sciber_yklocker package in edit mode
pip install -e .

# Install requirements and run tests
python -m tox

# Run linting
python -m tox -e lint

# Build binary
python -m tox -e build_win|build_linux|build_macos

## Binaries will be placd in ./build/

```

### Intune version of app:
This needs to be increased for Intune to roll out a new version of the app.
Current version: 1.0.0.6
- Version number is changed in [src/macos_utils/yubikey-locker-macos.spec](src/macos_utils/yubikey-locker-macos.spec)
- Version number is changed in [src\windows_utils\yubikey-locker.wxs](src/windows_utils/yubikey-locker.wxs)

### Linux prerequisites
Necessary to install a few packages:
```sudo apt install -y libpcsclite-dev swig pcscd```


### Windows install service

In case you do want to skip the MSI:
```
sc.exe create SciberYkLocker binPath="C:\Program Files\Sciber\YubiKeyLocker\yubikey-locker.exe" start=auto
sc.exe start SciberYkLocker```
