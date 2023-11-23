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
from ykman.device import list_all_devices, scan_devices

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

REG_REMOVALOPTION = "removalOption"
REG_TIMEOUT = "timeout"
REG_PATH = r"SOFTWARE\\Policies\\Yubico\\YubiKey Removal Behavior\\"


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
        self.yubikeyState = None

    def get_state(self):
        return self.yubikeyState

    def set_state(self, state):
        self.yubikeyState = state

    def get_timeout(self):
        return self.timeout

    def set_timeout(self, timeout):
        if isinstance(timeout, int):
            if timeout > 0:
                self.timeout = timeout

    def set_removal_option(self, method):
        if method == RemovalOption.LOCK or method == RemovalOption.LOGOUT:
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
        # This avoids connecting to the same YubiKey every loop. Only connect to it on state changes
        pids, new_state = scan_devices()
        if new_state != self.get_state():
            self.set_state(new_state)  # State has changed
            devices = list_all_devices()
            for device, info in devices:
                connected_message = f"YubiKey Connected with serial: {info.serial}"
                self.logger(connected_message)
            if len(devices) == 0:
                return False
        return True


def reg_create_key():
    try:
        return winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, REG_PATH)
    except (OSError, AttributeError):
        traceback.print_exc()
        return False


def reg_query_key(key_handle, key_name):
    try:
        # QueryValueEx returns a tuple, the value and the type
        # We assume our values are REG_SZ
        return (winreg.QueryValueEx(key_handle, key_name))[0]
    except (OSError, TypeError, FileNotFoundError, KeyError):
        traceback.print_exc()
        return False


def reg_set_key(key_handle, key_name, key_value):
    try:
        winreg.SetValueEx(key_handle, key_name, 0, winreg.REG_SZ, str(key_value))
        return True
    except (OSError, TypeError):
        traceback.print_exc()
        return False


def reg_handler(key_name, key_value):
    # Open / Create the key - need admin privs
    key_handle = reg_create_key()
    if key_handle:
        # Query the keyname for its value, if it does not exist create it with default value and try again.
        ret = reg_query_key(key_handle, key_name)
        if ret is False:
            # We need to set the value
            if reg_set_key(key_handle, key_name, key_value):
                # If successful, key_value is the new value in the registry
                ret = key_value

        # Close the key handle
        winreg.CloseKey(key_handle)

        if ret:
            return ret

    # Else
    return False


def reg_check_timeout(yklocker):
    # Call reg_handler with default values to use if registry is not populated
    timeoutValue = int(reg_handler(REG_TIMEOUT, yklocker.get_timeout()))
    if timeoutValue is not False:
        yklocker.set_timeout(timeoutValue)
    # Return current timeout
    return yklocker.get_timeout()


def reg_check_removal_option(yklocker):
    # Call reg_handler with default values to use if registry is not populated
    lockValue = reg_handler(REG_REMOVALOPTION, yklocker.get_removal_option())
    if lockValue is not False:
        yklocker.set_removal_option(lockValue)
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
    message2 = "Started scan for YubiKeys"

    yklocker.logger(message1)
    yklocker.logger(message2)

    loop = True
    while loop:
        sleep(yklocker.get_timeout())

        if get_my_platform() == MyPlatform.WIN:
            # Check for any timeout or RemovalOption updates from the registry
            reg_check_updates(yklocker)

            # Check if hWaitStop has been issued
            if (
                win32event.WaitForSingleObject(serviceObject.hWaitStop, 5000)
                == win32event.WAIT_OBJECT_0
            ):  # Then stop the loop
                loop = False

        if not yklocker.is_yubikey_connected():
            locking_message = "YubiKey Disconnected. Locking workstation"
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
    _svc_name_ = "SciberYkLocker"
    _svc_display_name_ = "Sciber YubiKey Locker"
    _svc_description_ = "To enable automatic lock when removing the YubiKey."

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
        servicemanager.PrepareToHMyPlatformtSingle(AppServerSvc)
        servicemanager.StartServiceCtrlDispatcher()
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
            elif opt == "-t":
                if arg.isdecimal():
                    timeout = int(arg)

        yklocker = init_yklocker(removal_option, timeout)
        loop_code(serviceObject=None, yklocker=yklocker)


if __name__ == "__main__":
    main(sys.argv[1:])  # pragma: no cover
