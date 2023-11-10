#General imports
import platform
from time import sleep
import getopt
from enum import Enum

#Yubikey imports
from ykman.device import list_all_devices, scan_devices

class OS(Enum):
    MAC = 0
    WIN = 1
    LX = 2
    UNKNOWN = -1

class lockMethod(Enum):
    LOCKOUT = 0
    LOGOUT = 1

class ykLock:
    def setLockMethod(self,method):
        self.lockType = method

    def getLockMethod(self):
        return self.lockType

    def lockMacOS(self):
        from ctypes import CDLL
        loginPF = CDLL('/System/Library/PrivateFrameworks/login.framework/Versions/Current/login')
        result = loginPF.SACLockScreenImmediate()

    def lockLinux(self):
        import os
        command = 'dbus-send --type=method_call --dest=org.gnome.ScreenSaver /org/gnome/ScreenSaver org.gnome.ScreenSaver.Lock'
        if self.getLockMethod() == lockMethod.LOGOUT:
            command= 'dbus-send --session --type=method_call --print-reply --dest=org.gnome.SessionManager /org/gnome/SessionManager org.gnome.SessionManager.Logout uint32:1'

        os.popen(command)

    def lockWindows(self):
        import win32process
        import win32con
        import win32ts
        import win32profile

        #As the service will be running as System you require a session handle to interact with the Desktop logon
        console_session_id = win32ts.WTSGetActiveConsoleSessionId()
        console_user_token = win32ts.WTSQueryUserToken(console_session_id)
        startup = win32process.STARTUPINFO()
        priority = win32con.NORMAL_PRIORITY_CLASS
        environment = win32profile.CreateEnvironmentBlock(console_user_token, False)

        # Determine what type of lock-action to take. Defaults to lock
        command = "\\Windows\\system32\\rundll32.exe user32.dll,LockWorkStation"
        if self.getLockMethod() == lockMethod.LOGOUT:
            command = "\\Windows\\system32\\logoff.exe"

        handle, thread_id ,pid, tid = win32process.CreateProcessAsUser(console_user_token, None, command, None, None, True, priority, environment, None, startup)

        
    def os_detect(self):
        if platform.system() == 'Darwin':
            self.osversion = OS.MAC
        elif platform.system() == 'Windows':
            self.osversion = OS.WIN
        elif platform.system() == 'Linux':
            self.osversion = OS.LX
        else:
            self.osversion = OS.UNKNOWN

    def getOS(self):
        return self.osversion


def windowsCode(yklocker,looptime):
    #Windows service dependancies
    import win32serviceutil
    import win32service
    import win32event
    import servicemanager
    import socket

    #Windows service definition
    class AppServerSvc (win32serviceutil.ServiceFramework):
        _svc_name_ = "SciberYkLocker"
        _svc_display_name_ = "Sciber YubiKey Locker"

        def __init__(self,args):
            win32serviceutil.ServiceFramework.__init__(self,args)
            self.hWaitStop = win32event.CreateEvent(None,0,0,None)
            socket.setdefaulttimeout(60)

        def SvcStop(self):
            self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
            win32event.SetEvent(self.hWaitStop)

        def SvcDoRun(self):
            servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                                servicemanager.PYS_SERVICE_STARTED,
                                (self._svc_name_,''))
            self.main()

        def main(self):
            servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                                servicemanager.PYS_SERVICE_STARTED,
                                (self._svc_name_,''))
            if yklocker.getLockMethod() == lockMethod.LOCKOUT:
                servicemanager.LogInfoMsg(f"Initiated Sciber-YkLocker with lockMethod LOCKOUT after {looptime} seconds without a detected YubiKey")
            else:
                servicemanager.LogInfoMsg(f"Initiated Sciber-YkLocker with lockMethod LOGOUT after {looptime} seconds without a detected YubiKey")

            servicemanager.LogInfoMsg("Started scan for YubiKeys")
            state = None
            while True:
                sleep(looptime)
                pids, new_state = scan_devices()
                if new_state != state:
                    state = new_state  # State has changed
                    for device, info in list_all_devices():
                        servicemanager.LogInfoMsg(f"YubiKey Connected with serial: {info.serial}")
                    if len(list_all_devices()) == 0:
                        servicemanager.LogInfoMsg(f"YubiKey Disconnected. Locking workstation")
                        yklocker.lockWindows()

                # Stops the loop if hWaitStop has been issued
                if win32event.WaitForSingleObject(self.hWaitStop, 5000) == win32event.WAIT_OBJECT_0: 
                    break

    #Start as a service in Windows
    servicemanager.Initialize()
    servicemanager.PrepareToHostSingle(AppServerSvc)
    servicemanager.StartServiceCtrlDispatcher()

    

def nixCode(yklocker,looptime):
    if yklocker.getLockMethod() == lockMethod.LOCKOUT:
        print(f"Initiated Sciber-YkLocker with lockMethod LOCKOUT after {looptime} seconds without a detected YubiKey")
    else:
        print(f"Initiated Sciber-YkLocker with lockMethod LOGOUT after {looptime} seconds without a detected YubiKey")

    print("Started scan for YubiKeys")
    state = None
    while True:
        sleep(looptime)
        pids, new_state = scan_devices()
        if new_state != state:
            state = new_state  # State has changed
            for device, info in list_all_devices():
                 print(f"YubiKey Connected with serial: {info.serial}")
            if len(list_all_devices()) == 0:
                print("YubiKey Disconnected. Locking workstation")
                if yklocker.getOS() == OS.LX:
                    yklocker.lockLinux()
                elif yklocker.getOS() == OS.MAC:
                    yklocker.lockMacOS()
            

def main(argv):
    # Create ykLock object
    yklocker = ykLock()
    yklocker.os_detect()

    # Set defaults
    yklocker.setLockMethod(lockMethod.LOCKOUT)
    default_looptime = 10

    opts, args = getopt.getopt(argv,"l:t:")
    for opt, arg in opts:
        if opt == '-l':
            if arg == "logout":
                yklocker.setLockMethod(lockMethod.LOGOUT)
        elif opt == '-t':
            if arg.isdecimal():
                newtime = int(arg)
                if newtime > 0:
                    default_looptime = newtime

    # All arguments have been parsed, initiate the next function
    if yklocker.getOS() == OS.WIN:
        windowsCode(yklocker,default_looptime)
    elif yklocker.getOS()  == OS.LX or yklocker.getOS()  == OS.MAC:
        nixCode(yklocker,default_looptime)
        




if __name__ == '__main__':
    import sys
    main(sys.argv[1:])


