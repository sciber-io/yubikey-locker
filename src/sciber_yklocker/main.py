# sciber_yklocker.py
# General imports
import getopt
import platform
import sys
from time import sleep


# Yubikey imports
from ykman.device import list_all_devices  # , scan_devices

from sciber_yklocker.lib import MyOS, RemovalOption

# Import platform specific code
if platform.system() == MyOS.WIN:
    from sciber_yklocker.lib_win import (
        check_service_interruption,
        lock_system,
        log_message,
        reg_check_removal_option,
        reg_check_timeout,
        reg_check_updates,
        win_main,
    )
elif platform.system() == MyOS.LX:
    from sciber_yklocker.lib_lx import lock_system, log_message

elif platform.system() == MyOS.MAC:
    from sciber_yklocker.lib_mac import lock_system, log_message


class YkLock:
    def __init__(self) -> None:
        # Set default values
        self.timeout: int = 10
        self.removal_option: RemovalOption = RemovalOption.NOTHING
        self.service_object = None

    def get_timeout(self) -> int:
        return self.timeout

    def set_timeout(self, timeout: int) -> None:
        if isinstance(timeout, int):
            if timeout > 0:
                self.timeout = timeout

    def get_removal_option(self) -> RemovalOption:
        return self.removal_option

    def set_removal_option(self, method: RemovalOption) -> None:
        if method in RemovalOption.__members__.values():
            self.removal_option = method

    def get_service_object(self):
        return self.service_object

    def set_service_object(self, service_object) -> None:
        self.service_object = service_object

    def lock(self) -> None:
        if self.get_removal_option() != RemovalOption.NOTHING:
            lock_system(self.get_removal_option())

    def logger(self, msg: str) -> None:
        log_message(msg)

    def is_yubikey_connected(self) -> bool:
        devices = list_all_devices()
        if len(devices) == 0:
            return False
        else:
            return True

    # Function to handle interruption signals sent to the program
    def continue_looping(self) -> bool:
        # Only the Windows service we need to check for incoming signals
        if platform.system() == MyOS.WIN:
            return check_service_interruption(self.get_service_object())

        return True


def loop_code(yklocker: YkLock) -> None:
    # Print start messages
    message1 = f"Initiated Sciber-YkLocker with RemovalOption {yklocker.get_removal_option()} after {yklocker.get_timeout()} seconds without a detected YubiKey"

    yklocker.logger(message1)

    while yklocker.continue_looping():
        sleep(yklocker.get_timeout())

        if platform.system() == MyOS.WIN:
            # Check for any timeout or RemovalOption updates from the registry
            reg_check_updates(yklocker)

        if not yklocker.is_yubikey_connected():
            locking_message = (
                f"YubiKey not found, action to take: {yklocker.get_removal_option()}"
            )
            yklocker.logger(locking_message)
            yklocker.lock()


def init_yklocker(removal_option: RemovalOption, timeout: int) -> YkLock:
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
    if platform.system() == MyOS.WIN:
        reg_check_timeout(yklocker)
        reg_check_removal_option(yklocker)

    return yklocker


def main(argv) -> None:
    # If Windows, start a service based on the class AppServerSvc
    if platform.system() == MyOS.WIN:
        win_main()
    # If LX or MAC, check arguments then initiate yklock object and then run code
    elif platform.system() == MyOS.LX or platform.system() == MyOS.MAC:
        # Default values
        removal_option: RemovalOption = RemovalOption.NOTHING
        timeout: int = 10

        # Check arguments
        opts, args = getopt.getopt(argv, "l:t:z")
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
            elif opt == "-z":
                # Used for execution and logging test
                yklocker = YkLock()
                yklocker.logger("Sciber-Yklocker test logging")
                sys.exit(0)

        yklocker = init_yklocker(removal_option, timeout)
        loop_code(yklocker=yklocker)


if __name__ == "__main__":
    main(sys.argv[1:])  # pragma: no cover
