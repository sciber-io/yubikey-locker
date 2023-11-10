#General imports
import platform
from time import sleep
import getopt

#Yubikey imports
from ykman.device import list_all_devices, scan_devices


class ykLock:
    def setLogoff(self):
        self.lockType = "logoff"
    def setLockOut(self):
        self.lockType = "lockout"
    def getLockType(self):
        return self.lockType

    def lockMacOS(self):
        from ctypes import CDLL
        loginPF = CDLL('/System/Library/PrivateFrameworks/login.framework/Versions/Current/login')
        result = loginPF.SACLockScreenImmediate()

    def lockLinux(self):
        import os
        command = 'dbus-send --type=method_call --dest=org.gnome.ScreenSaver /org/gnome/ScreenSaver org.gnome.ScreenSaver.Lock'
        if self.getLockType() == "logoff":
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
        if self.getLockType() == "logoff":
            command = "\\Windows\\system32\\logoff.exe"

        handle, thread_id ,pid, tid = win32process.CreateProcessAsUser(console_user_token, None, command, None, None, True, priority, environment, None, startup)

        
    def os_detect(self):
        if platform.system() == 'Darwin':
            self.osversion = 0
        elif platform.system() == 'Windows':
            self.osversion = 1
        elif platform.system() == 'Linux':
            self.osversion = 2
        else:
            self.osversion = -1

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

    

def nixCode(yklocker,os,looptime):
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
                if os == "lx":
                    yklocker.lockLinux()
                elif os == "mac":
                    yklocker.lockMacOS()
            

def main(argv):
    # Create ykLock object
    yklocker = ykLock()
    yklocker.os_detect()

    os = ""
    looptime = 10

    opts, args = getopt.getopt(argv,"o:l:t:",["ostype="])
    if len(opts) > 0:
        for opt, arg in opts:
            if opt == '-o':
                os = arg
            elif opt == '-l':
                if arg == "logoff":
                    yklocker.setLogoff()
            elif opt == '-t':
                if arg.isdecimal():
                    newtime = int(arg)
                    if newtime > 0:
                        looptime = newtime
            else:
                print("Please specify -o and the os <win,mac,lx> to start. Example: yklocker.exe -o win")

        # All arguments have been parsed, initiate the next function
        if os == "win":
            windowsCode(yklocker,looptime)
        elif os == "lx" or os == "mac":
            nixCode(yklocker,os,looptime)
        else: 
            print("Please specify win|mac|lx for -o")
    else:
        print("No arguments specified. Please specify -o and the os <win,mac,lx> to start. Example: yklocker.exe -o win")
    




if __name__ == '__main__':
    import sys
    main(sys.argv[1:])


