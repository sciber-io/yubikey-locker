# sciber_yklocker.py
# General imports
import getopt
import platform
import sys
from time import sleep

# Yubikey imports
from ykman.device import list_all_devices  # , scan_devices

from lib import MyPlatform, RemovalOption

# Import platform specific code
if platform.system() == "Windows":
    from lib_win import (
        check_service_interruption,
        lock_system,
        log_message,
        reg_check_removal_option,
        reg_check_timeout,
        reg_check_updates,
        win_main,
    )


elif platform.system() == "Linux":
    from lib_lx import lock_system, log_message

elif platform.system() == "Darwin":
    from lib_mac import lock_system, log_message


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
        self.removal_option = RemovalOption.NOTHING

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
            lock_system(self.get_removal_option())

    def logger(self, msg):
        log_message(msg)

    def is_yubikey_connected(self):
        devices = list_all_devices()
        if len(devices) == 0:
            return False
        else:
            return True

    # Function to handle interruption signals sent to the program
    def continue_looping(self, serviceObject):
        # Only the Windows service we need to check for incoming signals
        if get_my_platform() == MyPlatform.WIN:
            return check_service_interruption(serviceObject)

        return True


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


def main(argv):
    # If Windows, start a service based on the class AppServerSvc
    if get_my_platform() == MyPlatform.WIN:
        win_main()
    # If LX or MAC, check arguments then initiate yklock object and then run code
    elif get_my_platform() == MyPlatform.LX or get_my_platform() == MyPlatform.MAC:
        removal_option = None
        timeout = None

        # Check arguments
        opts, args = getopt.getopt(argv, "l:t:")
        for opt, arg in opts:
            if opt == "-l":
                if arg == RemovalOption.LOGOUT:
                    removal_option = RemovalOption.LOGOUT
                if arg == RemovalOption.LOCK:
                    removal_option = RemovalOption.LOCK
                elif arg == RemovalOption.NOTHING:
                    removal_option = RemovalOption.NOTHING
            elif opt == "-t":
                if arg.isdecimal():
                    timeout = int(arg)

        yklocker = init_yklocker(removal_option, timeout)
        loop_code(serviceObject=None, yklocker=yklocker)


if __name__ == "__main__":
    main(sys.argv[1:])  # pragma: no cover
