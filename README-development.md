
# YubiKey Autolocker by Sciber

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
