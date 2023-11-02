
#General imports
import platform
from time import sleep

#Yubikey imports
from ykman.device import list_all_devices, scan_devices

#Windows service dependancies
import win32serviceutil
import win32service
import win32event
import servicemanager
import socket

class ykLock:

    def lockMacOS(self):
        from ctypes import CDLL
        loginPF = CDLL('/System/Library/PrivateFrameworks/login.framework/Versions/Current/login')
        result = loginPF.SACLockScreenImmediate()

    def lockLinux(self):
         pass
    
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
         
#Windows service definition
class AppServerSvc (win32serviceutil.ServiceFramework):
    _svc_name_ = "SciberYkLocker"
    _svc_display_name_ = "Sciber Yubikey Locker"

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
        servicemanager.LogInfoMsg("Started scan for yubikeys")
        import win32process
        import win32con
        import win32ts
        import win32profile
        from ykman.device import list_all_devices, scan_devices
        state = None
        while True:
            sleep(10)
            pids, new_state = scan_devices()
            if new_state != state:
                state = new_state  # State has changed
                for device, info in list_all_devices():
                    servicemanager.LogInfoMsg(f"Yubikey Connected with serial: {info.serial}")
                if len(list_all_devices()) == 0:
                    servicemanager.LogInfoMsg(f"Yubikey Disconnected. Locking workstation")
                    console_session_id = win32ts.WTSGetActiveConsoleSessionId()
                    console_user_token = win32ts.WTSQueryUserToken(console_session_id)
                    startup = win32process.STARTUPINFO()
                    priority = win32con.NORMAL_PRIORITY_CLASS
                    environment = win32profile.CreateEnvironmentBlock(console_user_token, False)
                    handle, thread_id ,pid, tid = win32process.CreateProcessAsUser(console_user_token, None, "rundll32.exe user32.dll,LockWorkStation", None, None, True, priority, environment, None, startup)
            if win32event.WaitForSingleObject(self.hWaitStop, 5000) == win32event.WAIT_OBJECT_0: 
                break

def main(argv):

    import getopt

    opts, args = getopt.getopt(argv,"o:",["ostype="])
    for opt, arg in opts:
        if opt == '-o':
            if arg == "win":
                #win32serviceutil.HandleCommandLine(AppServerSvc)
                #To solve starting in a timely fashion....
                servicemanager.Initialize()
                servicemanager.PrepareToHostSingle(AppServerSvc)
                servicemanager.StartServiceCtrlDispatcher()
        else:
            print("Nein")

if __name__ == '__main__':
    import sys
    main(sys.argv[1:])


