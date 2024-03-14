import subprocess
from ctypes import CDLL

from pyoslog import OS_LOG_DEFAULT, os_log

from sciber_yklocker.models.removaloption import RemovalOption


def log_message(msg: str):
    os_log(OS_LOG_DEFAULT, msg)


def lock_system(removal_option: RemovalOption) -> None:
    if removal_option == RemovalOption.LOCK:
        loginPF = CDLL(
            "/System/Library/PrivateFrameworks/login.framework/Versions/Current/login"
        )
        loginPF.SACLockScreenImmediate()
    elif removal_option == RemovalOption.LOGOUT:
        subprocess.run(
            "/bin/launchctl bootout user/$(/usr/bin/id -u $(/usr/bin/whoami))",
            shell=True,
        )


# Unusued function for now
def have_yubikey_been_removed(timeout_in_seconds: int) -> bool:
    # Check the logs the last X seconds depending on how often the locker is configured to check the status
    command1 = f"/usr/bin/log show --last {timeout_in_seconds}s "
    command2 = """--predicate 'process = "icdd"'"""
    process = subprocess.Popen(
        command1 + command2, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
    )

    # If a line is logged with the following three keywords we determine that a YubiKey has been ejected from the device
    keyword1 = "Removed"
    keyword2 = "USB"
    keyword3 = "YubiKey"

    for line in process.stdout.readline():
        line = line.decode("utf-8")

        if (keyword1 in line) and (keyword2 in line) and (keyword3 in line):
            return True

    return False
