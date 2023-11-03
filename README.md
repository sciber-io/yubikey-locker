
# YubiKey Autolocker by Sciber

To enable automatic lock when removing the YubiKey. 

### Windows
1. Download sciber-yklocker.exe to at C:\Program Files\Sciber\sciber-yklocker\sciber-yklocker.exe  
2. Open a command shell as Administrator
3. Execute register-service.bat
4. Ensure you follow Jonas guide on his blog https://swjm.blog/locking-the-workstation-on-fido2-security-key-removal-part-2-80962c944c78 to set up GPO/Intune control to decide what you want to do if the YubiKey is removed.

### Linux
Download sciber-yklocker.linux and execute it in a terminal  

### Mac  
SoonTM

### Warning
Avoid running this tool without a YubiKey present as it will then lock your computer. 

### Credits
####  [Jonas Markström](https://github.com/JMarkstrom/YubiKey-Removal-Behavior).
Thank you for letting us reuse your AD/Intune templates to enable control via GPO's. Also thank you for the inspiration and discussions we have.
- https://github.com/JMarkstrom/YubiKey-Removal-Behavior
- https://swjm.blog/locking-the-workstation-on-fido2-security-key-removal-part-2-80962c944c78


### TODO:  
1. User choise between lockout and logout
