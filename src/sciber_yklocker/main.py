import getopt
import platform
import sys
from time import sleep

from sciber_yklocker.models.myos import MyOS
from sciber_yklocker.models.removaloption import RemovalOption
from sciber_yklocker.models.yklock import YkLock

# Import platform specific code
if platform.system() == MyOS.WIN:
    from sciber_yklocker.lib.win import (
        check_service_interruption,
        reg_check_removal_option,
        reg_check_timeout,
        reg_check_updates,
        win_main,
    )


# Function to handle interruption signals sent to the program
def continue_looping(yklocker: YkLock) -> bool:
    # Only the Windows service we need to check for incoming signals
    if platform.system() == MyOS.WIN:
        return check_service_interruption(yklocker.get_service_object())

    return True


def loop_code(yklocker: YkLock) -> None:
    # Print start messages
    message1 = f"Initiated YubiKeyLocker with RemovalOption {yklocker.get_removal_option()} after {yklocker.get_timeout()} seconds without a detected YubiKey"

    yklocker.logger(message1)

    while continue_looping(yklocker):
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


def check_arguments() -> tuple[RemovalOption, int]:
    # Default values
    removal_option: RemovalOption = None
    timeout: int | any = None

    # Check arguments
    opts, args = getopt.getopt(sys.argv[1:], "l:t:z")
    for opt, arg in opts:
        if opt == "-l":
            if arg == RemovalOption.LOGOUT:
                removal_option = RemovalOption.LOGOUT
            elif arg == RemovalOption.LOCK:
                removal_option = RemovalOption.LOCK
            elif arg == RemovalOption.NOTHING:
                removal_option = RemovalOption.NOTHING
            else:
                print("Invalid RemovalOption entered, defaulting to nothing")
        elif opt == "-t":
            if arg.isdecimal():
                timeout = int(arg)
            else:
                print("Invalid Timeout entered, defaulting to 10s")

        elif opt == "-z":
            # Used for execution and logging test
            yklocker = YkLock()
            yklocker.logger("YubiKeyLocker test logging")
            sys.exit(0)

    return removal_option, timeout


def main() -> None:
    # If Windows, start a service based on the class AppServerSvc
    if platform.system() == MyOS.WIN:
        win_main()
    # If LX or MAC, check arguments then initiate yklock object and then run code
    elif platform.system() == MyOS.LX or platform.system() == MyOS.MAC:
        removal_option, timeout = check_arguments()
        yklocker = init_yklocker(removal_option, timeout)
        loop_code(yklocker=yklocker)


if __name__ == "__main__":
    main()  # pragma: no cover
