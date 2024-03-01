import socket

import servicemanager
import win32con
import win32event
import win32process
import win32profile
import win32service
import win32serviceutil
import win32ts

from lib import RemovalOption


def lock_system(removal_option):
    # As the service will be running as System you require a session handle to interact with the Desktop logon
    console_session_id = win32ts.WTSGetActiveConsoleSessionId()
    console_user_token = win32ts.WTSQueryUserToken(console_session_id)
    startup = win32process.STARTUPINFO()
    priority = win32con.NORMAL_PRIORITY_CLASS
    environment = win32profile.CreateEnvironmentBlock(console_user_token, False)

    command = ""
    if removal_option == RemovalOption.LOCK:
        command = "\\Windows\\system32\\rundll32.exe user32.dll,LockWorkStation"
    elif removal_option == RemovalOption.LOGOUT:
        command = "\\Windows\\system32\\logoff.exe"

    handle, thread_id, pid, tid = win32process.CreateProcessAsUser(
        console_user_token,
        None,
        command,
        None,
        None,
        True,
        priority,
        environment,
        None,
        startup,
    )


def log_message(msg):
    servicemanager.LogInfoMsg(msg)


def check_service_interruption(serviceObject):
    # Check if hWaitStop has been issued
    if (
        win32event.WaitForSingleObject(serviceObject.hWaitStop, 5000)
        == win32event.WAIT_OBJECT_0
    ):  # Then stop the loop
        return False
    else:
        return True


# Windows Service Class Definition
class AppServerSvc(win32serviceutil.ServiceFramework):
    _svc_name_ = "SciberYklocker"
    _svc_display_name_ = "Sciber YubiKey Locker"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        socket.setdefaulttimeout(60)

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)

    def SvcDoRun(self):
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, ""),
        )
        from sciber_yklocker import init_yklocker, loop_code

        # instantiate a yklocker-object and start running the code
        yklocker = init_yklocker(None, None)
        # To handle service interruptions etc, pass the win service class instance along
        loop_code(serviceObject=self, yklocker=yklocker)


def win_main():
    servicemanager.Initialize()
    servicemanager.PrepareToHostSingle(AppServerSvc)
    try:
        servicemanager.StartServiceCtrlDispatcher()
    except SystemError:
        print("The executable needs to be installed and started as a service.")
