import socket
import traceback
import winreg

import servicemanager
import win32con
import win32event
import win32process
import win32profile
import win32service
import win32serviceutil
import win32ts

from sciber_yklocker.models.removaloption import RemovalOption


REG_REMOVALOPTION = "RemovalOption"
REG_TIMEOUT = "Timeout"
REG_PATH = r"SOFTWARE\\Policies\\Sciber\\YubiKey Removal Behavior\\"


def log_message(msg: str) -> None:
    servicemanager.LogInfoMsg(msg)


def lock_system(removal_option: RemovalOption) -> None:
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


# Windows Service Class Definition
class AppServerSvc(win32serviceutil.ServiceFramework):
    _svc_name_ = "SciberYklocker"
    _svc_display_name_ = "Sciber YubiKey Locker"

    def __init__(self, args) -> None:
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        socket.setdefaulttimeout(60)

    def SvcStop(self) -> None:
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)

    def SvcDoRun(self) -> None:
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, ""),
        )
        from sciber_yklocker.main import init_yklocker, loop_code

        # instantiate a yklocker-object and start running the code
        yklocker = init_yklocker(None, None)
        yklocker.set_service_object(self)

        # To handle service interruptions etc, pass the win service class instance along
        loop_code(yklocker=yklocker)


def check_service_interruption(serviceObject: AppServerSvc) -> bool:
    # Check if hWaitStop has been issued
    if (
        win32event.WaitForSingleObject(serviceObject.hWaitStop, 5000)
        == win32event.WAIT_OBJECT_0
    ):  # Then stop the loop
        return False
    else:
        return True


def reg_query_key(key_name: str):
    try:
        # Attemt to open the handle to registry
        key_handle = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, REG_PATH)
        # QueryValueEx returns a tuple, the value and the type
        ret = winreg.QueryValueEx(key_handle, key_name)[0]
        # Close the handle to the key
        key_handle.Close()
        return ret
    except (OSError, TypeError, FileNotFoundError, KeyError):
        traceback.print_exc()
        return False


def reg_check_timeout(yklocker) -> int:
    timeoutValue = int(reg_query_key(REG_TIMEOUT))
    if timeoutValue is not False:
        yklocker.set_timeout(timeoutValue)
    # Return current timeout
    return yklocker.get_timeout()


def reg_check_removal_option(yklocker) -> RemovalOption:
    lockValue = reg_query_key(REG_REMOVALOPTION)
    if lockValue is not False:
        yklocker.set_removal_option(lockValue)

    # Return current RemovalOption
    return yklocker.get_removal_option()


def reg_check_updates(yklocker) -> None:
    # check for changes in the registry
    timeoutValue = yklocker.get_timeout()
    removalOption = yklocker.get_removal_option()
    # Check registry and get the latest values
    timeoutValue2 = reg_check_timeout(yklocker)
    removalOption2 = reg_check_removal_option(yklocker)

    if timeoutValue != timeoutValue2 or removalOption != removalOption2:
        message = f"Updated Sciber-YkLocker with RemovalOption {yklocker.get_removal_option()} after {yklocker.get_timeout()} seconds without a detected YubiKey"
        yklocker.logger(message)


def win_main() -> None:
    servicemanager.Initialize()
    servicemanager.PrepareToHostSingle(AppServerSvc)
    try:
        servicemanager.StartServiceCtrlDispatcher()
    except SystemError:
        print("The executable needs to be installed and started as a service.")
