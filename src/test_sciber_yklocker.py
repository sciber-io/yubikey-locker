from unittest.mock import MagicMock, patch

import fake_winreg

from sciber_yklocker import (
    OS,
    initRegCheck,
    lockMethod,
    nixCode,
    os,
    platform,
    regcheck,
    regCreateKey,
    regQueryKey,
    regSetKey,
    win32con,
    win32process,
    win32profile,
    win32ts,
    ykLock,
)


def test_yklock_getsetLockMethod():
    yklocker = ykLock()
    input = lockMethod.LOGOUT
    yklocker.setLockMethod(input)
    yklocker.setLockMethod("hello")

    assert yklocker.getLockMethod() == input


def test_yklock_getsetTimeout():
    yklocker = ykLock()
    input = 15
    yklocker.setTimeout(input)
    yklocker.setTimeout("a")
    yklocker.setTimeout(-1)

    assert yklocker.getTimeout() == input


def test_yklock_get_os():
    orig = platform.system
    platform.system = lambda: "nada"
    yklocker = ykLock()

    assert yklocker.getOS() == OS.UNKNOWN
    platform.system = orig


def test_yklock_lock():
    # Test Linux lock
    platform.system = lambda: "Linux"
    linuxLocker = ykLock()
    with patch.object(os, "popen") as mock_popen:
        linuxLocker.lock()
        mock_popen.assert_called_with(
            "dbus-send --type=method_call --dest=org.gnome.ScreenSaver /org/gnome/ScreenSaver org.gnome.ScreenSaver.Lock"
        )

    # Test Windows Lock
    platform.system = lambda: "Windows"
    windowsLocker = ykLock()
    win32con.NORMAL_PRIORITY_CLASS = 0
    win32ts.WTSGetActiveConsoleSessionId = MagicMock()
    win32ts.WTSQueryUserToken = MagicMock()
    win32process.STARTUPINFO = MagicMock()
    win32profile.CreateEnvironmentBlock = MagicMock()
    win32process.CreateProcessAsUser = MagicMock(return_value=[0, 1, 2, 3])
    windowsLocker.lock()

    win32process.CreateProcessAsUser.assert_called_once()

    # Test Mac Lock
    platform.system = lambda: "Darwin"

    # Unclear how to mock this one


def test_regCreateKey():
    ret = regCreateKey(fake_winreg)

    # open key assumes the key has already been created
    ret1 = fake_winreg.OpenKey(
        fake_winreg.HKEY_LOCAL_MACHINE,
        r"SOFTWARE\\Policies\\Yubico\\YubiKey Removal Behavior\\",
    )
    assert ret.handle.full_key == ret1.handle.full_key


def test_regQueryKey():
    key_handle = regCreateKey(fake_winreg)
    # Non-existing key should return None
    assert regQueryKey(fake_winreg, key_handle, "nada") is None


def test_regSetKey():
    key_handle = regCreateKey(fake_winreg)
    # Successfully creating a key:value should return True
    ret = regSetKey(fake_winreg, key_handle, "name1", "value1")
    assert ret is True

    # Successfully querying that value should, return the value
    ret = regQueryKey(fake_winreg, key_handle, "name1")
    assert ret[0] == "value1"


def test_regcheck():
    input = lockMethod.LOGOUT
    ret = regcheck(fake_winreg, "removalOption", input)
    assert ret == input

    input = 15
    ret = regcheck(fake_winreg, "timeout", input)
    assert int(ret) == input


# Test new defaults
def test_initRegCheck():
    yklocker = ykLock()
    # Using different inputs than the defaults set in ykLock()
    input1 = lockMethod.LOGOUT
    input2 = 15
    yklocker.setLockMethod(input1)
    yklocker.setTimeout(input2)

    lockValue, timeoutValue = initRegCheck(fake_winreg, yklocker)
    assert lockValue == input1
    assert timeoutValue == input2


# Nerf lock-function
@patch.object(ykLock, "lock", return_value=False)
@patch("sciber_yklocker.scan_devices", return_value=[0, 1])
@patch("sciber_yklocker.list_all_devices", return_value=[])
def test_nixCode(mock_lock, mock_scan, mock_list):
    yklocker = ykLock()
    # Nerf sleep
    yklocker.getTimeout = lambda: 0

    nixCode(yklocker)
    mock_scan.assert_called_once()
    mock_lock.assert_called_once()
    mock_list.assert_called_once()
