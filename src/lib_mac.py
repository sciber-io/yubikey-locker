import syslog

import CDLL

from lib import RemovalOption


def log_message(msg):
    syslog.syslog(syslog.LOG_INFO, msg)


def lock_system(removal_option):
    if removal_option == RemovalOption.LOCK:
        loginPF = CDLL(
            "/System/Library/PrivateFrameworks/login.framework/Versions/Current/login"
        )
        loginPF.SACLockScreenImmediate()
