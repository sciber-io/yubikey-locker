# sciber_yklocker.py

# General imports
import getopt
import os
import platform
import sys
import traceback
from ctypes import CDLL
from enum import Enum, StrEnum  # StrEnum is python 3.11+
from time import sleep

# Yubikey imports
from ykman.device import list_all_devices  # , scan_devices

# Enable Windows global imports
# If not reassigned - code running on Linux/Mac would break
if platform.system() != "Windows":
    import EmptyModule

    # Modules only used by the Windows service
    sys.modules["win32con"] = EmptyModule
    sys.modules["win32process"] = EmptyModule
    sys.modules["win32profile"] = EmptyModule
    sys.modules["win32ts"] = EmptyModule
    sys.modules["socket"] = EmptyModule
    sys.modules["win32ts"] = EmptyModule
    sys.modules["servicemanager"] = EmptyModule
    sys.modules["win32event"] = EmptyModule
    sys.modules["win32service"] = EmptyModule
    sys.modules["win32serviceutil"] = EmptyModule
    sys.modules["winreg"] = EmptyModule

import socket
import winreg

import servicemanager
import win32con
import win32event
import win32process
import win32profile
import win32service
import win32serviceutil
import win32ts

REG_REMOVALOPTION = "RemovalOption"
REG_TIMEOUT = "Timeout"
REG_PATH = r"SOFTWARE\\Policies\\Sciber\\YubiKey Removal Behavior\\"


class MyPlatform(Enum):
    MAC = 0
    WIN = 1
    LX = 2
    UNKNOWN = -1


class RemovalOption(StrEnum):
    LOCK = "Lock"
    LOGOUT = "Logout"
    NOTHING = "doNothing"


def get_my_platform():
    if platform.system() == "Darwin":
        return MyPlatform.MAC
    elif platform.system() == "Windows":
        return MyPlatform.WIN
    elif platform.system() == "Linux":
        return MyPlatform.LX
    else:
        return MyPlatform.UNKNOWN


class YkLock:
    def __init__(self):
        # Set default values
        self.MyPlatformversion = get_my_platform()
        self.timeout = 10
        self.removal_option = RemovalOption.LOCK

    def get_timeout(self):
        return self.timeout

    def set_timeout(self, timeout):
        if isinstance(timeout, int):
            if timeout > 0:
                self.timeout = timeout

    def set_removal_option(self, method):
        if method in RemovalOption.__members__.values():
            self.removal_option = method

    def get_removal_option(self):
        return self.removal_option

    def lock(self):
        if self.get_removal_option() != RemovalOption.NOTHING:
            if self.MyPlatformversion == MyPlatform.MAC:
                loginPF = CDLL(
                    "/System/Library/PrivateFrameworks/login.framework/Versions/Current/login"
                )
                loginPF.SACLockScreenImmediate()
            elif self.MyPlatformversion == MyPlatform.LX:
                # Determine what type of lock-action to take. Defaults to lock
                command = "dbus-send --type=method_call --dest=org.gnome.ScreenSaver /org/gnome/ScreenSaver org.gnome.ScreenSaver.Lock"
                if self.get_removal_option() == RemovalOption.LOGOUT:
                    command = "dbus-send --session --type=method_call --print-reply --dest=org.gnome.SessionManager /org/gnome/SessionManager org.gnome.SessionManager.Logout uint32:1"

                os.popen(command)
            elif self.MyPlatformversion == MyPlatform.WIN:
                # As the service will be running as System you require a session handle to interact with the Desktop logon
                console_session_id = win32ts.WTSGetActiveConsoleSessionId()
                console_user_token = win32ts.WTSQueryUserToken(console_session_id)
                startup = win32process.STARTUPINFO()
                priority = win32con.NORMAL_PRIORITY_CLASS
                environment = win32profile.CreateEnvironmentBlock(
                    console_user_token, False
                )

                # Determine what type of lock-action to take. Defaults to lock
                command = "\\Windows\\system32\\rundll32.exe user32.dll,LockWorkStation"
                if self.get_removal_option() == RemovalOption.LOGOUT:
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

    def logger(self, message):
        if self.MyPlatformversion == MyPlatform.WIN:
            servicemanager.LogInfoMsg(message)
        else:
            print(message)

    def is_yubikey_connected(self):
        devices = list_all_devices()
        if len(devices) == 0:
            return False
        else:
            return True

    def continue_looping(self, serviceObject):
        # Function to handle interruptions signal sent to the program
        if get_my_platform() == MyPlatform.WIN:
            # Check if hWaitStop has been issued
            if (
                win32event.WaitForSingleObject(serviceObject.hWaitStop, 5000)
                == win32event.WAIT_OBJECT_0
            ):  # Then stop the loop
                return False

        return True


def reg_query_key(key_name):
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


def reg_check_timeout(yklocker):
    timeoutValue = int(reg_query_key(REG_TIMEOUT))
    if timeoutValue is not False:
        yklocker.set_timeout(timeoutValue)
    # Return current timeout
    return yklocker.get_timeout()


def reg_check_removal_option(yklocker):
    lockValue = reg_query_key(REG_REMOVALOPTION)
    if lockValue is not False:
        yklocker.set_removal_option(lockValue)
    else:
        # If no Windows Registry option is set. Default to doNothing
        yklocker.set_removal_option(RemovalOption.NOTHING)
    # Return current RemovalOption
    return yklocker.get_removal_option()


def reg_check_updates(yklocker):
    # check for changes in the registry
    timeoutValue = yklocker.get_timeout()
    removalOption = yklocker.get_removal_option()
    # Check registry and get the latest values
    timeoutValue2 = reg_check_timeout(yklocker)
    removalOption2 = reg_check_removal_option(yklocker)

    if timeoutValue != timeoutValue2 or removalOption != removalOption2:
        message = f"Updated Sciber-YkLocker with RemovalOption {yklocker.get_removal_option()} after {yklocker.get_timeout()} seconds without a detected YubiKey"
        yklocker.logger(message)


def loop_code(serviceObject, yklocker):
    # Print start messages
    message1 = f"Initiated Sciber-YkLocker with RemovalOption {yklocker.get_removal_option()} after {yklocker.get_timeout()} seconds without a detected YubiKey"

    yklocker.logger(message1)

    while yklocker.continue_looping(serviceObject):
        sleep(yklocker.get_timeout())

        if get_my_platform() == MyPlatform.WIN:
            # Check for any timeout or RemovalOption updates from the registry
            reg_check_updates(yklocker)

        if not yklocker.is_yubikey_connected():
            locking_message = "YubiKey not found. Locking workstation"
            yklocker.logger(locking_message)
            yklocker.lock()


def init_yklocker(removal_option, timeout):
    # Used order for settings
    # 1. Windows Registry
    # 2. CommandLine Arguments
    # 3. Defaults

    # Create YkLock object with default settings
    yklocker = YkLock()

    # Override defaults with CommandLine Arguments
    if removal_option is not None:
        yklocker.set_removal_option(removal_option)

    if timeout is not None:
        yklocker.set_timeout(timeout)

    # If Windows - Check registry to override settings
    if get_my_platform() == MyPlatform.WIN:
        reg_check_timeout(yklocker)
        reg_check_removal_option(yklocker)

    return yklocker


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
        # instantiate a yklocker-object and start running the code
        yklocker = init_yklocker(None, None)
        # To handle service interruptions etc, pass the win service class instance along
        loop_code(serviceObject=self, yklocker=yklocker)


def main(argv):
    # If Windows, start a service based on the class AppServerSvc
    if get_my_platform() == MyPlatform.WIN:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(AppServerSvc)
        try:
            servicemanager.StartServiceCtrlDispatcher()
        except SystemError:
            print("The executable needs to be installed and started as a service.")
    # If LX or MAC, check arguments then initiate yklock object and then run code
    elif get_my_platform() == MyPlatform.LX or get_my_platform() == MyPlatform.MAC:
        removal_option = RemovalOption.LOCK
        timeout = 10

        # Check arguments
        opts, args = getopt.getopt(argv, "l:t:")
        for opt, arg in opts:
            if opt == "-l":
                if arg == RemovalOption.LOGOUT:
                    removal_option = RemovalOption.LOGOUT
                elif arg == RemovalOption.NOTHING:
                    removal_option = RemovalOption.NOTHING
            elif opt == "-t":
                if arg.isdecimal():
                    timeout = int(arg)

        yklocker = init_yklocker(removal_option, timeout)
        loop_code(serviceObject=None, yklocker=yklocker)


if __name__ == "__main__":
    main(sys.argv[1:])  # pragma: no cover
