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

# Enable Windows global imports plus testing
if platform.system() != "Windows":
    import emptyModule

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


class ykLock:
    def getOS(self):
        return self.osversion

    def os_detect(self):
        if platform.system() == "Darwin":
            self.osversion = OS.MAC
        elif platform.system() == "Windows":
            self.osversion = OS.WIN
        elif platform.system() == "Linux":
            self.osversion = OS.LX
        else:
            self.osversion = OS.UNKNOWN

    def __init__(self):
        # Set default values
        self.os_detect()
        self.timeout = 10
        self.lockType = lockMethod.LOCK

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
        # Keep the looping going
        return True

    def logger(self, message):
        if self.osversion == OS.WIN:
            servicemanager.LogInfoMsg(message)
        else:
            print(message)


def regCreateKey():
    try:
        return winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, REG_PATH)
    except (OSError, AttributeError):
        traceback.print_exc()
        return False


def regQueryKey(key_handle, key_name):
    try:
        return winreg.QueryValueEx(key_handle, key_name)
    except (OSError, TypeError):
        traceback.print_exc()
        return False


def regSetKey(key_handle, key_name, key_value):
    try:
        winreg.SetValueEx(key_handle, key_name, 0, winreg.REG_SZ, str(key_value))
        return True
    except (OSError, TypeError):
        traceback.print_exc()
        return False


def regcheck(key_name, key_value):
    # Open / Create the key - need admin privs
    key_handle = regCreateKey()
    if key_handle:
        # Query the keyname for its value, if it does not exist create it with default value and try again.
        ret = regQueryKey(key_handle, key_name)
        if ret is False:
            # We need to set the value
            if regSetKey(key_handle, key_name, key_value):
                # Then sanity check by getting it
                ret = regQueryKey(key_handle, key_name)

        # Close the key handle
        winreg.CloseKey(key_handle)

        if ret:
            return ret[0]

    # Else
    return False


def initRegCheck(yklocker):
    # Call regcheck with default values to use if registry is not populated
    lockValue = regcheck(REG_REMOVALOPTION, yklocker.getLockMethod())
    if lockValue is not False:
        yklocker.setLockMethod(lockValue)

    # Call regcheck with default values to use if registry is not populated
    timeoutValue = int(regcheck(REG_TIMEOUT, yklocker.getTimeout()))
    if timeoutValue is not False:
        yklocker.setTimeout(timeoutValue)

    return lockValue, timeoutValue


def windowsCheckRegUpdates(yklocker):
    # check for changes in the registry
    timeoutValue = yklocker.getTimeout()
    removalOption = yklocker.getLockMethod()
    initRegCheck(yklocker)
    timeoutValue2 = yklocker.getTimeout()
    removalOption2 = yklocker.getLockMethod()

    if timeoutValue != timeoutValue2 or removalOption != removalOption2:
        servicemanager.LogInfoMsg(
            f"Updated Sciber-YkLocker with lockMethod {yklocker.getLockMethod()} after {yklocker.getTimeout()} seconds without a detected YubiKey"
        )


def loopCode(serviceObject, yklocker):
    # Print start messages
    message1 = f"Initiated Sciber-YkLocker with lockMethod {yklocker.getLockMethod()} after {yklocker.getTimeout()} seconds without a detected YubiKey"
    message2 = "Started scan for YubiKeys"

    yklocker.logger(message1)
    yklocker.logger(message2)

    state = None
    loop = True
    while loop:
        sleep(yklocker.getTimeout())

        # If windows, check for any updates from the registry
        if yklocker.getOS() == OS.WIN:
            windowsCheckRegUpdates(yklocker)

        pids, new_state = scan_devices()
        if new_state != state:
            state = new_state  # State has changed
            devices = list_all_devices()
            for device, info in devices:
                connected_message = f"YubiKey Connected with serial: {info.serial}"
                yklocker.logger(connected_message)
            if len(devices) == 0:
                locking_message = "YubiKey Disconnected. Locking workstation"
                yklocker.logger(locking_message)
                loop = yklocker.lock()

        if yklocker.getOS() == OS.WIN:
            # Stops the loop if hWaitStop has been issued
            if (
                win32event.WaitForSingleObject(serviceObject.hWaitStop, 5000)
                == win32event.WAIT_OBJECT_0
            ):
                loop = False


def windowsService(yklocker):
    # Windows service definition
    class AppServerSvc(win32serviceutil.ServiceFramework):
        _svc_name_ = "SciberYkLocker"
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
            self.main()

        def main(self):
            servicemanager.LogMsg(
                servicemanager.EVENTLOG_INFORMATION_TYPE,
                servicemanager.PYS_SERVICE_STARTED,
                (self._svc_name_, ""),
            )

            # Go into the loop checking for connected YubiKeys
            loopCode(self, yklocker)

    # Start the AppServerSvc-class as a service in Windows
    #
    servicemanager.Initialize()
    servicemanager.PrepareToHostSingle(AppServerSvc)
    servicemanager.StartServiceCtrlDispatcher()


def main(argv):
    # Create ykLock object
    yklocker = ykLock()

    # If Windows check registry settings to override defaults:
    if yklocker.getOS() == OS.WIN:
        initRegCheck(yklocker)

    # Check arguments to override defaults:
    opts, args = getopt.getopt(argv, "l:t:")
    for opt, arg in opts:
        if opt == "-l":
            if arg == lockMethod.LOGOUT:
                yklocker.setLockMethod(lockMethod.LOGOUT)
        elif opt == "-t":
            if arg.isdecimal():
                yklocker.setTimeout(int(arg))

    # All arguments have been parsed, initiate the next function
    if yklocker.getOS() == OS.WIN:
        windowsService(yklocker)
    elif yklocker.getOS() == OS.LX or yklocker.getOS() == OS.MAC:
        loopCode(None, yklocker)


if __name__ == "__main__":
    main(sys.argv[1:])
