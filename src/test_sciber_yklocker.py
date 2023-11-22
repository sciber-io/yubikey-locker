from unittest.mock import MagicMock, patch

import fake_winreg

from sciber_yklocker import (
    OS,
    initRegCheck,
    lockMethod,
    loopCode,
    os,
    platform,
    regcheck,
    regCreateKey,
    regQueryKey,
    regSetKey,
    windowsCheckRegUpdates,
    windowsService,
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
    platform.system = lambda: "nada"
    yklocker = ykLock()

    assert yklocker.getOS() == OS.UNKNOWN


def test_yklock_lockLinux():
    # Test Linux lock
    platform.system = lambda: "Linux"
    linuxLocker = ykLock()
    with patch.object(os, "popen") as mock_popen:
        linuxLocker.lock()
        mock_popen.assert_called_with(
            "dbus-send --type=method_call --dest=org.gnome.ScreenSaver /org/gnome/ScreenSaver org.gnome.ScreenSaver.Lock"
        )


@patch("sciber_yklocker.win32con")
@patch("sciber_yklocker.win32ts")
@patch("sciber_yklocker.win32process")
@patch("sciber_yklocker.win32profile")
def test_yklock_lockWindows(m_win32profile, m_win32process, m_win32ts, m_win32con):
    platform.system = lambda: "Windows"
    windowsLocker = ykLock()
    m_win32con.NORMAL_PRIORITY_CLASS = 0
    # win32ts.WTSGetActiveConsoleSessionId = MagicMock()
    m_win32ts.WTSQueryUserToken = MagicMock()
    # m_win32process.STARTUPINFO = MagicMock()
    m_win32profile.CreateEnvironmentBlock = MagicMock()
    m_win32process.CreateProcessAsUser = MagicMock(return_value=[0, 1, 2, 3])
    windowsLocker.lock()

    m_win32process.CreateProcessAsUser.assert_called_once()


@patch("sciber_yklocker.CDLL")
def test_yklock_lockMac(mock_CDLL):
    # Test Mac Lock
    platform.system = lambda: "Darwin"
    macLocker = ykLock()
    macLocker.lock()

    mock_CDLL.assert_called_once()


def reg_reset():
    # Delete our values
    try:
        key_handle = fake_winreg.OpenKey(
            fake_winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\\Policies\\Yubico\\YubiKey Removal Behavior\\",
        )

        fake_winreg.DeleteValue(key_handle, "removalOption")
        fake_winreg.DeleteValue(key_handle, "timeout")
    except OSError:
        print("No registry values to delete")


def test_regCreateKey():
    reg_reset()
    with patch("sciber_yklocker.winreg", fake_winreg):
        ret = regCreateKey()

        # open key assumes the key has already been created
        ret1 = fake_winreg.OpenKey(
            fake_winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\\Policies\\Yubico\\YubiKey Removal Behavior\\",
        )
        assert ret.handle.full_key == ret1.handle.full_key


def test_regQueryKey():
    reg_reset()
    with patch("sciber_yklocker.winreg", fake_winreg):
        key_handle = regCreateKey()
        # Non-existing key should return None
        assert regQueryKey(key_handle, "nada") is False


def test_regSetKey():
    reg_reset()
    with patch("sciber_yklocker.winreg", fake_winreg):
        key_handle = regCreateKey()
        # Successfully creating a key:value should return True
        ret = regSetKey(key_handle, "name1", "value1")
        assert ret is True

        # Successfully querying that value should, return the value
        ret = regQueryKey(key_handle, "name1")
        assert ret[0] == "value1"


def test_regcheck():
    reg_reset()
    with patch("sciber_yklocker.winreg", fake_winreg):
        input = lockMethod.LOGOUT
        ret = regcheck("removalOption", input)
        assert ret == input

        input = 15
        ret = regcheck("timeout", input)
        assert int(ret) == input


# Test new defaults
def test_initRegCheck():
    reg_reset()
    with patch("sciber_yklocker.winreg", fake_winreg):
        yklocker = ykLock()
        # Using different inputs than the defaults set in ykLock()
        input1 = lockMethod.LOGOUT
        input2 = 15
        yklocker.setLockMethod(input1)
        yklocker.setTimeout(input2)

        lockValue, timeoutValue = initRegCheck(yklocker)
        assert lockValue == input1
        assert timeoutValue == input2


@patch("sciber_yklocker.servicemanager")
def test_windowsCheckRegUpdates_noUpdate(m_servicemanager):
    reg_reset()
    platform.system = lambda: "Windows"
    winlocker = ykLock()
    input1 = lockMethod.LOCK
    input2 = 11
    winlocker.setLockMethod(input1)
    winlocker.setTimeout(input2)

    with patch("sciber_yklocker.winreg", fake_winreg):
        windowsCheckRegUpdates(winlocker)

    m_servicemanager.LogInfoMsg.assert_not_called()
    assert winlocker.getLockMethod() == input1
    assert winlocker.getTimeout() == input2


@patch("sciber_yklocker.servicemanager")
def test_windowsCheckRegUpdates_withUpdate(m_servicemanager):
    reg_reset()
    platform.system = lambda: "Windows"
    winlocker = ykLock()
    input1 = lockMethod.LOCK
    input2 = 11
    winlocker.setLockMethod(input1)
    winlocker.setTimeout(input2)

    def mock_regQueryKey(key_name, key_value):
        print("mock_regQueryKey")
        print(key_name, key_value)
        #
        if key_value == "removalOption":
            return ["logout", fake_winreg.REG_SZ]
        elif key_value == "timeout":
            return ["15", fake_winreg.REG_SZ]

    with patch("sciber_yklocker.regQueryKey", mock_regQueryKey):
        with patch("sciber_yklocker.winreg", fake_winreg):
            windowsCheckRegUpdates(winlocker)

    m_servicemanager.LogInfoMsg.assert_called_once()
    assert winlocker.getLockMethod() != input1
    assert winlocker.getTimeout() != input2


# Nerf lock-function and patch ykman imports
@patch.object(ykLock, "lock", return_value=False)
@patch("sciber_yklocker.scan_devices", return_value=[0, 1])
@patch("sciber_yklocker.list_all_devices", return_value=[])
# Patch other called imports
@patch("sciber_yklocker.servicemanager")
@patch("sciber_yklocker.win32event")
def test_loopCode(m_win32event, m_servicemanager, mock_list, mock_scan, mock_lock):
    platform.system = lambda: "Windows"
    winlocker = ykLock()
    # Nerf sleep
    winlocker.getTimeout = lambda: 0
    with patch("sciber_yklocker.winreg", fake_winreg):
        loopCode(MagicMock(), winlocker)
    m_servicemanager.LogInfoMsg.call_count == 3
    m_win32event.WaitForSingleObject.assert_called_once()
    mock_scan.assert_called_once()
    mock_lock.assert_called_once()
    mock_list.assert_called_once()


@patch("sciber_yklocker.servicemanager")
@patch("sciber_yklocker.win32serviceutil")
def test_windowsService(m_win32serviceutil, m_servicemanager):
    platform.system = lambda: "Windows"
    winlocker = ykLock()
    m_servicemanager.StartServiceCtrlDispatcher = MagicMock()
    m_win32serviceutil.ServiceFramework = MagicMock()
    windowsService(winlocker)

    # Make sure the code calls StartServiceCtrlDispatcher
    m_servicemanager.StartServiceCtrlDispatcher.assert_called_once()
    m_win32serviceutil.ServiceFramework.assert_not_called()
