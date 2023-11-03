# pyinstaller -F --paths=".\venv\lib\site-packages" -n "sciber-yklocker" ..\src\sciber-yklocker.py

echo "Linux build initiated"
pyinstaller -F -n "sciber-yklocker" ../src/sciber-yklocker.py