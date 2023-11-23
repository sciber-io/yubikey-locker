from unittest.mock import MagicMock, patch

import fake_winreg

from sciber_yklocker import (
    OS,
    REG_PATH,
    REG_REMOVALOPTION,
    REG_TIMEOUT,
    AppServerSvc,
    getOS,
    initYklocker,
    lockMethod,
    loopCode,
    main,
    os,
    platform,
    regCheckRemovalOption,
    regCheckTimeout,
    regCheckUpdates,
    regCreateKey,
    regHandler,
    regQueryKey,
    regSetKey,
    servicemanager,
    socket,
    win32event,
    win32service,
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


## Test Functions ##


def test_getOS():
    platform.system = lambda: "nada"
    assert getOS() == OS.UNKNOWN


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


@patch("sciber_yklocker.scan_devices", return_value=[0, 1])
def test_ykLock_isYubikeyConnected_false(_):
    platform.system = lambda: "Windows"
    winlocker = ykLock()

    # Patch logger to catch the message sent to it
    with patch("sciber_yklocker.ykLock.logger", MagicMock()) as mock_logger:
        # Make sure no YubiKeys are found by return an empty array
        with patch("sciber_yklocker.list_all_devices", lambda: []):
            assert winlocker.isYubikeyConnected() is False

        mock_logger.assert_not_called()


@patch("sciber_yklocker.scan_devices", return_value=[0, 1])
def test_ykLock_isYubikeyConnected_true(_):
    platform.system = lambda: "Windows"
    winlocker = ykLock()

    # Patch logger to catch the serial sent to it
    with patch("sciber_yklocker.ykLock.logger", MagicMock()) as mock_logger:
        # Make sure one "YubiKey" is found
        with patch("sciber_yklocker.list_all_devices", mock_list_one_device):
            assert winlocker.isYubikeyConnected() is True
        # Make sure we got the right serial
        assert "0123456789#" in mock_logger.call_args[0][0]


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
        assert regQueryKey(key_handle, REG_TIMEOUT) is input
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
        assert ret == "value1"

        fake_winreg.CloseKey(key_handle)


def test_regSetKey_error():
    reg_reset()
    # Use fake registry
    with patch("sciber_yklocker.winreg", fake_winreg):
        # "1" is an invalid key handle
        assert regSetKey("1", "2", "3") is False


def test_regHandler():
    # No real key handle to close so mock winreg
    with patch("sciber_yklocker.winreg", MagicMock()):
        # Our key handle
        with patch("sciber_yklocker.regCreateKey", lambda: True):
            # Assume no previous entries in the registry
            with patch("sciber_yklocker.regQueryKey", lambda a, b: False):
                # Mock successful key create
                with patch("sciber_yklocker.regSetKey", MagicMock()) as mock_set:
                    assert regHandler("a", "woo") == "woo"
                    mock_set.assert_called_once()


def test_regHandler_error():
    # Our key handle is True
    with patch("sciber_yklocker.regCreateKey", lambda: False):
        assert regHandler("a", "b") is False


def test_regCheckTimeout():
    yklocker = ykLock()
    # Assume the registry returns 15
    with patch("sciber_yklocker.regHandler", lambda a, b: "15"):
        regCheckTimeout(yklocker)

    assert yklocker.getTimeout() == 15


def test_regCheckTimeout_error():
    yklocker = ykLock()
    # Check with another value than the default
    yklocker.setTimeout(15)
    with patch("sciber_yklocker.regHandler", lambda a, b: False):
        regCheckTimeout(yklocker)

    assert yklocker.getTimeout() == 15


def test_regCheckRemovalOption():
    yklocker = ykLock()
    # Assume the registry returns logout
    with patch("sciber_yklocker.regHandler", lambda a, b: lockMethod.LOGOUT):
        regCheckRemovalOption(yklocker)

    assert yklocker.getLockMethod() == lockMethod.LOGOUT


def test_regCheckRemovalOption_error():
    yklocker = ykLock()
    # Check with another value than the default
    yklocker.setLockMethod(lockMethod.LOGOUT)
    with patch("sciber_yklocker.regHandler", lambda a, b: False):
        regCheckRemovalOption(yklocker)

    assert yklocker.getLockMethod() == lockMethod.LOGOUT


def test_regCheckUpdates_no_update():
    yklocker = ykLock()

    # No updates just return the default values
    with patch("sciber_yklocker.regCheckTimeout", lambda a: yklocker.getTimeout()):
        with patch(
            "sciber_yklocker.regCheckRemovalOption", lambda a: yklocker.getLockMethod()
        ):
            with patch("sciber_yklocker.ykLock.logger", MagicMock()) as mock_logger:
                regCheckUpdates(yklocker)
                # Logger should not have been called. No new values.
                mock_logger.assert_not_called()


def test_regCheckUpdates_with_update():
    yklocker = ykLock()

    # Updates from registy are non-default values:
    with patch("sciber_yklocker.regCheckTimeout", lambda a: 15):
        with patch(
            "sciber_yklocker.regCheckRemovalOption", lambda a: lockMethod.LOGOUT
        ):
            with patch("sciber_yklocker.ykLock.logger", MagicMock()) as mock_logger:
                regCheckUpdates(yklocker)
                # Logger should not have been called. No new values.
                mock_logger.assert_called_once()


@patch.object(ykLock, "lock")
@patch("sciber_yklocker.servicemanager")
# Make sure we trigger the service interruption to quit the loop
def test_loopCode_no_yubikey_windows(m_servicemanager, mock_lock):
    platform.system = lambda: "Windows"
    winlocker = ykLock()
    # Patch sleep and connection
    winlocker.getTimeout = lambda: 0
    winlocker.isYubikeyConnected = lambda: False

    # Mock win32event constant and function
    mock_win32event = win32event
    mock_win32event.WAIT_OBJECT_0 = 0
    mock_win32event.WaitForSingleObject = lambda a, b: 0

    # Patch logger to catch messages
    with patch("sciber_yklocker.ykLock.logger", MagicMock()) as mock_logger:
        loopCode(MagicMock(), winlocker)

        # Make sure we got the right message
        mock_logger.assert_called_with("YubiKey Disconnected. Locking workstation")

    # Make sure lock was called, no arguments expected
    mock_lock.assert_called_once_with()


@patch.object(ykLock, "lock")
@patch("sciber_yklocker.servicemanager")
# Make sure we trigger the service interruption to quit the loop
def test_loopCode_with_yubikey_windows(m_servicemanager, mock_lock):
    platform.system = lambda: "Windows"
    winlocker = ykLock()
    # Patch sleep and connection
    winlocker.getTimeout = lambda: 0
    winlocker.isYubikeyConnected = lambda: True

    # Mock win32event constant and function
    mock_win32event = win32event
    mock_win32event.WAIT_OBJECT_0 = 0
    mock_win32event.WaitForSingleObject = lambda a, b: 0

    # Patch logger to catch messages
    with patch("sciber_yklocker.ykLock.logger", MagicMock()):
        loopCode(MagicMock(), winlocker)
    # Make sure lock was not called
    mock_lock.assert_not_called()


def test_initYklocker():
    platform.system = lambda: "Windows"
    # Call the function with non-default settings and verify them
    with patch("sciber_yklocker.regCheckTimeout", MagicMock()) as mock_regCheckTimeout:
        with patch(
            "sciber_yklocker.regCheckRemovalOption", MagicMock()
        ) as mock_regCheckRemovalOption:
            yklocker = initYklocker(lockMethod.LOGOUT, 15)

            # Make sure gets were called but dont enter the functions
            mock_regCheckRemovalOption.assert_called_once()
            mock_regCheckTimeout.assert_called_once()

    assert yklocker.getLockMethod() == lockMethod.LOGOUT
    assert yklocker.getTimeout() == 15


def AppServerSvc__init__():
    # Instantiate the object and test its __init__ functionality
    # Make sure the expected function and content is there
    with patch(
        "win32serviceutil.ServiceFramework.__init__", MagicMock()
    ) as mock_svcinit:
        mock_win32event = win32event
        mock_win32event.CreateEvent = MagicMock()
        mock_socket = socket
        mock_socket.setdefaulttimeout = MagicMock()
        # Call the function
        win_service = AppServerSvc([""])

        mock_svcinit.assert_called_once()
        mock_win32event.CreateEvent.assert_called_once()
        mock_socket.setdefaulttimeout.assert_called_once()

    return win_service


def AppServerSvc_SvcDoRun(win_service):
    # Dont go inte the loop but make sure it was called
    with patch("sciber_yklocker.loopCode", MagicMock()) as mock_loopCode:
        with patch("sciber_yklocker.initYklocker", MagicMock()) as mock_initYklocker:
            mock_servicemanager = servicemanager
            mock_servicemanager.LogMsg = MagicMock()
            mock_servicemanager.PYS_SERVICE_STARTED = 0
            mock_servicemanager.EVENTLOG_INFORMATION_TYPE = 0

            # Call the function
            win_service.SvcDoRun()
            mock_servicemanager.LogMsg.assert_called_once()
            mock_initYklocker.assert_called_once()
            mock_loopCode.assert_called_once()


def AppServerSvc_SvcStop(win_service):
    win_service.ReportServiceStatus = MagicMock()
    win_service.hWaitStop = 0
    mock_win32service = win32service
    mock_win32service.SERVICE_STOP_PENDING = 0
    mock_win32event = win32event
    mock_win32event.SetEvent = MagicMock()

    # Call the function
    win_service.SvcStop()

    win_service.ReportServiceStatus.assert_called_once()
    mock_win32event.SetEvent.assert_called_once()


def test_AppServerSvc():
    win_service = AppServerSvc__init__()
    AppServerSvc_SvcDoRun(win_service)
    AppServerSvc_SvcStop(win_service)


@patch("sciber_yklocker.servicemanager")
def test_main_win(m_servicemanager):
    platform.system = lambda: "Windows"

    m_servicemanager.StartServiceCtrlDispatcher = MagicMock()
    main("")

    # Make sure the code calls StartServiceCtrlDispatcher
    m_servicemanager.StartServiceCtrlDispatcher.assert_called_once()


def test_main_no_args():
    platform.system = lambda: "Linux"
    # Dont go inte the loop but make sure it was called
    with patch("sciber_yklocker.loopCode", MagicMock()) as mock_loopCode:
        with patch("sciber_yklocker.initYklocker", MagicMock()) as mock_initYklocker:
            main([""])
            mock_loopCode.assert_called_once()
            mock_initYklocker.assert_called_once()


def test_main_other_with_args():
    platform.system = lambda: "Linux"
    # Dont go inte the loop but make sure it was called
    with patch("sciber_yklocker.loopCode", MagicMock()) as mock_loopCode:
        with patch("sciber_yklocker.initYklocker", MagicMock()) as mock_initYklocker:
            main(["-l", "logout", "-t", "5"])
            mock_loopCode.assert_called_once()
            mock_initYklocker.assert_called_once_with(lockMethod.LOGOUT, 5)
