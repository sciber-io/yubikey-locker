from pyoslog import os_log, OS_LOG_DEFAULT
from ctypes import CDLL
import subprocess

from sciber_yklocker.lib import RemovalOption


def log_message(msg):
    os_log(OS_LOG_DEFAULT, msg)


def lock_system(removal_option):
    if removal_option == RemovalOption.LOCK:
        loginPF = CDLL(
            "/System/Library/PrivateFrameworks/login.framework/Versions/Current/login"
        )
        loginPF.SACLockScreenImmediate()
    elif removal_option == RemovalOption.LOGOUT:
        subprocess.run(
            "/usr/bin/launchctl bootout user/$(/usr/bin/id -u $(/usr/bin/whoami))",
        )
