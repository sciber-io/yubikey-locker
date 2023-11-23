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
    import emptyModule

    # Modules only used by the Windows service
    sys.modules["win32con"] = emptyModule
    sys.modules["win32process"] = emptyModule
    sys.modules["win32profile"] = emptyModule
    sys.modules["win32ts"] = emptyModule
    sys.modules["socket"] = emptyModule
    sys.modules["win32ts"] = emptyModule
    sys.modules["servicemanager"] = emptyModule
    sys.modules["win32event"] = emptyModule
    sys.modules["win32service"] = emptyModule
    sys.modules["win32serviceutil"] = emptyModule
    sys.modules["winreg"] = emptyModule

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


class OS(Enum):
    MAC = 0
    WIN = 1
    LX = 2
    UNKNOWN = -1


class lockMethod(StrEnum):
    LOCK = "lock"
    LOGOUT = "logout"


def getOS():
    if platform.system() == "Darwin":
        return OS.MAC
    elif platform.system() == "Windows":
        return OS.WIN
    elif platform.system() == "Linux":
        return OS.LX
    else:
        return OS.UNKNOWN


class ykLock:
    def __init__(self):
        # Set default values
        self.osversion = getOS()
        self.timeout = 10
        self.lockType = lockMethod.LOCK
        self.yubikeyState = None

    def getState(self):
        return self.yubikeyState

    def setState(self, state):
        self.yubikeyState = state

    def getTimeout(self):
        return self.timeout

    def setTimeout(self, timeout):
        if isinstance(timeout, int):
            if timeout > 0:
                self.timeout = timeout

    def setLockMethod(self, method):
        if method == lockMethod.LOCK or method == lockMethod.LOGOUT:
            self.lockType = method

    def getLockMethod(self):
        return self.lockType

    def lock(self):
        if self.osversion == OS.MAC:
            loginPF = CDLL(
                "/System/Library/PrivateFrameworks/login.framework/Versions/Current/login"
            )
            loginPF.SACLockScreenImmediate()
        elif self.osversion == OS.LX:
            # Determine what type of lock-action to take. Defaults to lock
            command = "dbus-send --type=method_call --dest=org.gnome.ScreenSaver /org/gnome/ScreenSaver org.gnome.ScreenSaver.Lock"
            if self.getLockMethod() == lockMethod.LOGOUT:
                command = "dbus-send --session --type=method_call --print-reply --dest=org.gnome.SessionManager /org/gnome/SessionManager org.gnome.SessionManager.Logout uint32:1"

            os.popen(command)
        elif self.osversion == OS.WIN:
            # As the service will be running as System you require a session handle to interact with the Desktop logon
            console_session_id = win32ts.WTSGetActiveConsoleSessionId()
            console_user_token = win32ts.WTSQueryUserToken(console_session_id)
            startup = win32process.STARTUPINFO()
            priority = win32con.NORMAL_PRIORITY_CLASS
            environment = win32profile.CreateEnvironmentBlock(console_user_token, False)

            # Determine what type of lock-action to take. Defaults to lock
            command = "\\Windows\\system32\\rundll32.exe user32.dll,LockWorkStation"
            if self.getLockMethod() == lockMethod.LOGOUT:
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
        if self.osversion == OS.WIN:
            servicemanager.LogInfoMsg(message)
        else:
            print(message)

    def isYubikeyConnected(self):
        # This avoids connecting to the same YubiKey every loop. Only connect to it on state changes
        pids, new_state = scan_devices()
        if new_state != self.getState():
            self.setState(new_state)  # State has changed
            devices = list_all_devices()
            for device, info in devices:
                connected_message = f"YubiKey Connected with serial: {info.serial}"
                self.logger(connected_message)
            if len(devices) == 0:
                return False
        return True


def regCreateKey():
    try:
        return winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, REG_PATH)
    except (OSError, AttributeError):
        traceback.print_exc()
        return False


def regQueryKey(key_handle, key_name):
    try:
        # QueryValueEx returns a tuple, the value and the type
        # We assume our values are REG_SZ
        return (winreg.QueryValueEx(key_handle, key_name))[0]
    except (OSError, TypeError, FileNotFoundError, KeyError):
        traceback.print_exc()
        return False


def regSetKey(key_handle, key_name, key_value):
    try:
        winreg.SetValueEx(key_handle, key_name, 0, winreg.REG_SZ, str(key_value))
        return True
    except (OSError, TypeError):
        traceback.print_exc()
        return False


def regHandler(key_name, key_value):
    # Open / Create the key - need admin privs
    key_handle = regCreateKey()
    if key_handle:
        # Query the keyname for its value, if it does not exist create it with default value and try again.
        ret = regQueryKey(key_handle, key_name)
        if ret is False:
            # We need to set the value
            if regSetKey(key_handle, key_name, key_value):
                # If successful, key_value is the new value in the registry
                ret = key_value

        # Close the key handle
        winreg.CloseKey(key_handle)

        if ret:
            return ret

    # Else
    return False


def regCheckTimeout(yklocker):
    # Call regHandler with default values to use if registry is not populated
    timeoutValue = int(regHandler(REG_TIMEOUT, yklocker.getTimeout()))
    if timeoutValue is not False:
        yklocker.setTimeout(timeoutValue)
    # Return current timeout
    return yklocker.getTimeout()


def regCheckRemovalOption(yklocker):
    # Call regHandler with default values to use if registry is not populated
    lockValue = regHandler(REG_REMOVALOPTION, yklocker.getLockMethod())
    if lockValue is not False:
        yklocker.setLockMethod(lockValue)
    # Return current lockmethod
    return yklocker.getLockMethod()


def regCheckUpdates(yklocker):
    # check for changes in the registry
    timeoutValue = yklocker.getTimeout()
    removalOption = yklocker.getLockMethod()
    # Check registry and get the latest values
    timeoutValue2 = regCheckTimeout(yklocker)
    removalOption2 = regCheckRemovalOption(yklocker)

    if timeoutValue != timeoutValue2 or removalOption != removalOption2:
        message = f"Updated Sciber-YkLocker with lockMethod {yklocker.getLockMethod()} after {yklocker.getTimeout()} seconds without a detected YubiKey"
        yklocker.logger(message)


def loopCode(serviceObject, yklocker):
    # Print start messages
    message1 = f"Initiated Sciber-YkLocker with lockMethod {yklocker.getLockMethod()} after {yklocker.getTimeout()} seconds without a detected YubiKey"
    message2 = "Started scan for YubiKeys"

    yklocker.logger(message1)
    yklocker.logger(message2)

    loop = True
    while loop:
        sleep(yklocker.getTimeout())

        if getOS() == OS.WIN:
            # Check for any timeout or lockmethod updates from the registry
            regCheckUpdates(yklocker)

            # Check if hWaitStop has been issued
            if (
                win32event.WaitForSingleObject(serviceObject.hWaitStop, 5000)
                == win32event.WAIT_OBJECT_0
            ):  # Then stop the loop
                loop = False

        if not yklocker.isYubikeyConnected():
            locking_message = "YubiKey Disconnected. Locking workstation"
            yklocker.logger(locking_message)
            yklocker.lock()


def initYklocker(lockType, timeout):
    # Used order for settings
    # 1. Windows Registry
    # 2. CommandLine Arguments
    # 3. Defaults

    # Create ykLock object with default settings
    yklocker = ykLock()

    # Override defaults with CommandLine Arguments
    if lockType is not None:
        yklocker.setLockMethod(lockType)

    if timeout is not None:
        yklocker.setTimeout(timeout)

    # If Windows - Check registry to override settings
    if getOS() == OS.WIN:
        regCheckTimeout(yklocker)
        regCheckRemovalOption(yklocker)

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
        yklocker = initYklocker(None, None)
        # To handle service interruptions etc, pass the win service class instance along
        loopCode(serviceObject=self, yklocker=yklocker)


def main(argv):
    # If Windows, start a service based on the class AppServerSvc
    if getOS() == OS.WIN:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(AppServerSvc)
        servicemanager.StartServiceCtrlDispatcher()
    # If LX or MAC, check arguments then initiate yklock object and then run code
    elif getOS() == OS.LX or getOS() == OS.MAC:
        lockType = lockMethod.LOCK
        timeout = 10

        # Check arguments
        opts, args = getopt.getopt(argv, "l:t:")
        for opt, arg in opts:
            if opt == "-l":
                if arg == lockMethod.LOGOUT:
                    lockType = lockMethod.LOGOUT
            elif opt == "-t":
                if arg.isdecimal():
                    timeout = int(arg)

        yklocker = initYklocker(lockType, timeout)
        loopCode(serviceObject=None, yklocker=yklocker)


if __name__ == "__main__":
    main(sys.argv[1:])  # pragma: no cover
