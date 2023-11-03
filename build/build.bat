:: pyinstaller --clean -F --paths=".\venv\lib\site-packages" -n "sciber-yklocker" ..\src\sciber-yklocker.py
@echo off
echo "Windows build initiated"
pyinstaller --clean -F -n "sciber-yklocker" "..\src\sciber-yklocker.py"
echo "Windows Pyinstaller finished"