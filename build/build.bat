@echo off
echo "Windows build initiated"
pyinstaller --clean -F -n "sciber-yklocker" "..\src\sciber-yklocker.py"
echo "Windows Pyinstaller finished"