import os
import syslog

from sciber_yklocker.lib import RemovalOption


def log_message(msg: str):
    syslog.syslog(syslog.LOG_INFO, msg)


def lock_system(removal_option: RemovalOption) -> None:
    # Determine what type of lock-action to take
    command = ""
    if removal_option == RemovalOption.LOCK:
        command = "dbus-send --type=method_call --dest=org.gnome.ScreenSaver /org/gnome/ScreenSaver org.gnome.ScreenSaver.Lock"
    if removal_option == RemovalOption.LOGOUT:
        # pkill -SIGKILL -u $(whoami)
        command = "dbus-send --session --type=method_call --print-reply --dest=org.gnome.SessionManager /org/gnome/SessionManager org.gnome.SessionManager.Logout uint32:1"

    os.popen(command)
