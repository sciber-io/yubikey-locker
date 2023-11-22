from unittest.mock import MagicMock, patch

import fake_winreg

from sciber_yklocker import (
    OS,
    REG_PATH,
    REG_REMOVALOPTION,
    REG_TIMEOUT,
    initRegCheck,
    lockMethod,
    loopCode,
    main,
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


### Helper Functions ##
def reg_reset():
    # Delete our values
    try:
        key_handle = fake_winreg.OpenKey(fake_winreg.HKEY_LOCAL_MACHINE, REG_PATH)

        fake_winreg.DeleteValue(key_handle, REG_REMOVALOPTION)
        fake_winreg.DeleteValue(key_handle, REG_TIMEOUT)
        fake_winreg.DeleteKey(key_handle, REG_REMOVALOPTION)
        fake_winreg.DeleteKey(key_handle, REG_TIMEOUT)
        fake_winreg.CloseKey(key_handle)

    except OSError:
        print("No registry values to delete")


def mock_regQueryKey(key_name, key_value):
    print("mock_regQueryKey")
    print(key_name, key_value)
    #
    if key_value == REG_REMOVALOPTION:
        return [lockMethod.LOGOUT, fake_winreg.REG_SZ]
    elif key_value == REG_TIMEOUT:
        return ["15", fake_winreg.REG_SZ]


def mock_list_one_device():
    class info:
        serial = "0123456789#"

    mydict = {"A": "devices", "B": info}
    devices = []
    devices.append(mydict.values())

    return devices


def mock_list_no_devices():
    return []


def mock_scan_devices():
    return [0, 1]


def mock_WaitForSingleObject(a, b):
    return 0


## Test Functions ##


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
        mock_popen.assert_called_once()
        assert "ScreenSaver.Lock" in mock_popen.call_args[0][0]


def test_yklock_logoutLinux():
    # Test Linux logout
    platform.system = lambda: "Linux"
    linuxLocker = ykLock()
    linuxLocker.setLockMethod(lockMethod.LOGOUT)
    with patch.object(os, "popen") as mock_popen:
        linuxLocker.lock()
        mock_popen.assert_called_once()
        assert "SessionManager.Logout" in mock_popen.call_args[0][0]


@patch("sciber_yklocker.win32con")
@patch("sciber_yklocker.win32ts")
@patch("sciber_yklocker.win32process")
@patch("sciber_yklocker.win32profile")
def test_yklock_lockWindows(m_win32profile, m_win32process, m_win32ts, m_win32con):
    platform.system = lambda: "Windows"
    windowsLocker = ykLock()
    m_win32con.NORMAL_PRIORITY_CLASS = 0
    m_win32ts.WTSQueryUserToken = MagicMock()
    m_win32profile.CreateEnvironmentBlock = MagicMock()
    m_win32process.CreateProcessAsUser = MagicMock(return_value=[0, 1, 2, 3])

    # Test Windows LOCK
    windowsLocker.lock()
    m_win32process.CreateProcessAsUser.assert_called_once()
    assert "LockWorkStation" in m_win32process.CreateProcessAsUser.call_args[0][2]


@patch("sciber_yklocker.win32con")
@patch("sciber_yklocker.win32ts")
@patch("sciber_yklocker.win32process")
@patch("sciber_yklocker.win32profile")
def test_yklock_logoutWindows(m_win32profile, m_win32process, m_win32ts, m_win32con):
    platform.system = lambda: "Windows"
    windowsLocker = ykLock()
    windowsLocker.setLockMethod(lockMethod.LOGOUT)

    m_win32con.NORMAL_PRIORITY_CLASS = 0
    m_win32ts.WTSQueryUserToken = MagicMock()
    m_win32profile.CreateEnvironmentBlock = MagicMock()
    m_win32process.CreateProcessAsUser = MagicMock(return_value=[0, 1, 2, 3])

    # Test Windows LOGOUT
    windowsLocker.lock()
    m_win32process.CreateProcessAsUser.assert_called_once()
    assert "logoff.exe" in m_win32process.CreateProcessAsUser.call_args_list[0][0][2]


@patch("sciber_yklocker.CDLL")
def test_yklock_lockMac(mock_CDLL):
    # Test Mac Lock
    platform.system = lambda: "Darwin"
    macLocker = ykLock()
    macLocker.lock()

    mock_CDLL.assert_called_once()


@patch("sciber_yklocker.servicemanager")
def test_yklock_logger_windows(m_servicemanager):
    platform.system = lambda: "Windows"
    winlocker = ykLock()
    with patch("sciber_yklocker.servicemanager.LogInfoMsg") as mock_log:
        winlocker.logger("testmessage")
        mock_log.assert_called_once_with("testmessage")


def test_yklock_logger():
    platform.system = lambda: "Linux"
    linuxLocker = ykLock()
    with patch("builtins.print") as mock_print:
        linuxLocker.logger("testmessage")
        mock_print.assert_called_once_with("testmessage")


def test_regCreateKey():
    reg_reset()
    # Use fake registry
    with patch("sciber_yklocker.winreg", fake_winreg):
        create_key_handle = regCreateKey()

        # open key assumes the key has already been created
        open_key_handle = fake_winreg.OpenKey(fake_winreg.HKEY_LOCAL_MACHINE, REG_PATH)
        assert create_key_handle.handle.full_key == open_key_handle.handle.full_key
        fake_winreg.CloseKey(create_key_handle)
        fake_winreg.CloseKey(open_key_handle)


# Test non-existing registry
def test_regCreateKey_error():
    reg_reset()
    with patch("sciber_yklocker.winreg", None):
        assert regCreateKey() is False


def test_regQueryKey():
    reg_reset()
    # Use fake registry
    with patch("sciber_yklocker.winreg", fake_winreg):
        input = "1"
        key_handle = regCreateKey()
        regSetKey(key_handle, REG_TIMEOUT, input)
        assert regQueryKey(key_handle, REG_TIMEOUT)[0] is input
        fake_winreg.CloseKey(key_handle)


def test_regQueryKey_error():
    reg_reset()
    # Use fake registry
    with patch("sciber_yklocker.winreg", fake_winreg):
        key_handle = regCreateKey()
        # Non-existing key should return None
        assert regQueryKey(key_handle, "nada") is False
        fake_winreg.CloseKey(key_handle)


def test_regSetKey():
    reg_reset()
    # Use fake registry
    with patch("sciber_yklocker.winreg", fake_winreg):
        key_handle = regCreateKey()
        # Successfully creating a key:value should return True
        ret = regSetKey(key_handle, "name1", "value1")
        assert ret is True

        # Successfully querying that value should, return the value
        ret = regQueryKey(key_handle, "name1")
        assert ret[0] == "value1"

        fake_winreg.CloseKey(key_handle)


def test_regSetKey_error():
    reg_reset()
    # Use fake registry
    with patch("sciber_yklocker.winreg", fake_winreg):
        assert regSetKey("1", "2", "3") is False


def test_regcheck_removaloption():
    reg_reset()
    # Use fake registry
    with patch("sciber_yklocker.winreg", fake_winreg):
        input = lockMethod.LOGOUT
        assert regcheck(REG_REMOVALOPTION, input) == input


def test_regcheck_timeout():
    reg_reset()
    # Use fake registry
    with patch("sciber_yklocker.winreg", fake_winreg):
        input = 15
        assert int(regcheck(REG_TIMEOUT, input)) == input


def test_test_regcheck_error():
    reg_reset()
    # Use no registry
    with patch("sciber_yklocker.winreg", None):
        assert regcheck("1", "2") is False


# Test new defaults
def test_initRegCheck():
    reg_reset()
    # Use fake registry
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
def test_windowsCheckRegUpdates_no_update(m_servicemanager):
    reg_reset()
    # Use fake registry
    with patch("sciber_yklocker.winreg", fake_winreg):
        platform.system = lambda: "Windows"
        winlocker = ykLock()
        input1 = lockMethod.LOCK
        input2 = 11
        winlocker.setLockMethod(input1)
        winlocker.setTimeout(input2)

        windowsCheckRegUpdates(winlocker)

        m_servicemanager.LogInfoMsg.assert_not_called()
        assert winlocker.getLockMethod() == input1
        assert winlocker.getTimeout() == input2


@patch("sciber_yklocker.servicemanager")
def test_windowsCheckRegUpdates_with_update(m_servicemanager):
    reg_reset()
    # Use fake registry
    with patch("sciber_yklocker.winreg", fake_winreg):
        platform.system = lambda: "Windows"
        winlocker = ykLock()
        input1 = lockMethod.LOCK
        input2 = 10
        winlocker.setLockMethod(input1)
        winlocker.setTimeout(input2)

        # Call windowsCheckRegUpdates where it will find updates in the registry
        with patch("sciber_yklocker.regQueryKey", mock_regQueryKey):
            windowsCheckRegUpdates(winlocker)

        m_servicemanager.LogInfoMsg.assert_called_once()
        assert winlocker.getLockMethod() != input1
        assert winlocker.getTimeout() != input2


@patch.object(ykLock, "lock")
@patch("sciber_yklocker.scan_devices", return_value=[0, 1])
@patch("sciber_yklocker.servicemanager")
@patch("sciber_yklocker.win32event")
def test_loopCode_no_yubikey_windows(m_win32event, m_servicemanager, _, mock_lock):
    platform.system = lambda: "Windows"
    winlocker = ykLock()
    # Nerf sleep and infinitive loop
    winlocker.getTimeout = lambda: 0
    winlocker.isTest = lambda: True

    with patch(
        "sciber_yklocker.win32event.WaitForSingleObject", mock_WaitForSingleObject
    ):
        # Patch logger to catch the message sent to it
        with patch("sciber_yklocker.ykLock.logger", MagicMock()) as mock_logger:
            # Make sure no YubiKeys are found
            with patch("sciber_yklocker.list_all_devices", mock_list_no_devices):
                loopCode(MagicMock(), winlocker)

            # Make sure we got the right serial
            mock_logger.assert_called_with("YubiKey Disconnected. Locking workstation")
        # Make sure lock was called
        mock_lock.assert_called_once()


@patch.object(ykLock, "lock")
@patch("sciber_yklocker.scan_devices", return_value=[0, 1])
@patch("sciber_yklocker.servicemanager")
@patch("sciber_yklocker.win32event")
def test_loopCode_with_yubikey_windows(
    m_win32event, m_servicemanager, m_scan, mock_lock
):
    platform.system = lambda: "Windows"
    winlocker = ykLock()
    # Nerf sleep and infinitive loop
    winlocker.getTimeout = lambda: 0
    winlocker.isTest = lambda: True

    with patch(
        "sciber_yklocker.win32event.WaitForSingleObject", mock_WaitForSingleObject
    ):
        # Patch logger to catch the serial sent to it
        with patch("sciber_yklocker.ykLock.logger", MagicMock()) as mock_logger:
            # Make sure one "YubiKey" is found
            with patch("sciber_yklocker.list_all_devices", mock_list_one_device):
                loopCode(MagicMock(), winlocker)
            # Make sure we got the right serial
            assert "0123456789#" in mock_logger.call_args[0][0]
        # Make sure lock was not called
        mock_lock.assert_not_called()


@patch.object(ykLock, "lock")
@patch("sciber_yklocker.scan_devices", return_value=[0, 1])
def test_loopCode_no_yubikey(_, mock_lock):
    platform.system = lambda: "Linux"
    lxlocker = ykLock()
    # Nerf sleep and infinitive loop
    lxlocker.getTimeout = lambda: 0
    lxlocker.isTest = lambda: True

    # Patch logger to catch the message sent to it
    with patch("sciber_yklocker.ykLock.logger", MagicMock()) as mock_logger:
        # Make sure no YubiKeys are found
        with patch("sciber_yklocker.list_all_devices", mock_list_no_devices):
            loopCode(MagicMock(), lxlocker)

        # Make sure we got the right serial
        mock_logger.assert_called_with("YubiKey Disconnected. Locking workstation")
    # Make sure lock was called
    mock_lock.assert_called_once()


@patch.object(ykLock, "lock")
@patch("sciber_yklocker.scan_devices", return_value=[0, 1])
def test_loopCode_with_yubikey(_, mock_lock):
    platform.system = lambda: "Linux"
    lxlocker = ykLock()
    # Nerf sleep and infinitive loop
    lxlocker.getTimeout = lambda: 0
    lxlocker.isTest = lambda: True

    # Patch logger to catch the serial sent to it
    with patch("sciber_yklocker.ykLock.logger", MagicMock()) as mock_logger:
        # Make sure one "YubiKey" is found
        with patch("sciber_yklocker.list_all_devices", mock_list_one_device):
            loopCode(MagicMock(), lxlocker)
        # Make sure we got the right serial
        assert "0123456789#" in mock_logger.call_args[0][0]
    # Make sure lock was not called
    mock_lock.assert_not_called()


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


def test_main_windows_no_args():
    platform.system = lambda: "Windows"
    with patch("sciber_yklocker.ykLock.setLockMethod", MagicMock()) as mock_lockMethod:
        with patch("sciber_yklocker.initRegCheck", MagicMock()):
            with patch(
                "sciber_yklocker.windowsService", MagicMock()
            ) as mock_winservice:
                main([""])
            mock_winservice.assert_called_once()

        mock_lockMethod.assert_not_called()


def test_main_windows_with_args():
    platform.system = lambda: "Windows"
    with patch("sciber_yklocker.ykLock.setLockMethod", MagicMock()) as mock_lockMethod:
        with patch("sciber_yklocker.ykLock.setTimeout", MagicMock()) as mock_timeout:
            with patch("sciber_yklocker.initRegCheck", MagicMock()):
                with patch(
                    "sciber_yklocker.windowsService", MagicMock()
                ) as mock_winservice:
                    main(["-l", "logout", "-t", "5"])
                    mock_winservice.assert_called_once()
            mock_timeout.assert_called_once_with(5)
        mock_lockMethod.assert_called_once_with("logout")


def test_main_other_no_args():
    platform.system = lambda: "Linux"
    with patch("sciber_yklocker.ykLock.setLockMethod", MagicMock()) as mock_lockMethod:
        with patch("sciber_yklocker.loopCode", MagicMock()) as mock_loopCode:
            main([""])
        mock_loopCode.assert_called_once()

    mock_lockMethod.assert_not_called()


def test_main_other_with_args():
    platform.system = lambda: "Linux"
    with patch("sciber_yklocker.ykLock.setLockMethod", MagicMock()) as mock_lockMethod:
        with patch("sciber_yklocker.ykLock.setTimeout", MagicMock()) as mock_timeout:
            with patch("sciber_yklocker.loopCode", MagicMock()) as mock_loopCode:
                main(["-l", "logout", "-t", "5"])
                mock_loopCode.assert_called_once
            mock_timeout.assert_called_once_with(5)
        mock_lockMethod.assert_called_once_with("logout")
