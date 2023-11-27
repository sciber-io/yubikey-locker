if [ "$(uname)" == "Darwin" ]; then
echo "Linux build initiated"
pyinstaller -F -n "sciber-yklocker" ../src/sciber-yklocker.py

fi
# MacOS specifics:
if [ "$(uname)" == "Darwin" ]; then
echo "MacOS build initiated"
pyinstaller -F -n "sciber-yklocker" ../src/sciber-yklocker.py
# --windowed
# Get the macos-version of the application to move itself into the desired location, put plist in place, kill itself and start the plist?

  # https://pyinstaller.org/en/v4.1/usage.html#building-mac-os-x-app-bundles

  # https://medium.com/@fahimhossain_16989/adding-startup-scripts-to-launch-daemon-on-mac-os-x-sierra-10-12-6-7e0318c74de1

fi
