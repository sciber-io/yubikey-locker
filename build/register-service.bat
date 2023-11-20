
sc.exe create SciberYkLocker binPath="C:\Program Files\Sciber\sciber-yklocker\sciber-yklocker.exe" start=auto
sc.exe start SciberYkLocker

::sc config SciberYkLocker binPath="C:\Program Files\Sciber\sciber-yklocker\sciber-yklocker.exe -t 20 -l logoff" start=auto
