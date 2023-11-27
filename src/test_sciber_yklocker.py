from unittest.mock import MagicMock, patch

import fake_winreg

from sciber_yklocker import (
    REG_PATH,
    REG_REMOVALOPTION,
    REG_TIMEOUT,
    AppServerSvc,
    MyPlatform,
    RemovalOption,
    YkLock,
    get_my_platform,
    init_yklocker,
    loop_code,
    main,
    os,
    platform,
    reg_check_removal_option,
    reg_check_timeout,
    reg_check_updates,
    reg_create_key,
    reg_handler,
    reg_query_key,
    reg_set_key,
    servicemanager,
    socket,
    win32event,
    win32service,
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


def mock_list_one_device():
    class info:
        serial = "0123456789#"

    mydict = {"A": "devices", "B": info}
    devices = []
    devices.append(mydict.values())

    return devices


## Test Functions ##


def test_get_my_platform():
    platform.system = lambda: "nada"
    assert get_my_platform() == MyPlatform.UNKNOWN


def test_yklock_getset_removal_option():
    yklocker = YkLock()
    yklocker.set_removal_option(RemovalOption.LOGOUT)
    yklocker.set_removal_option("hello")
    assert yklocker.get_removal_option() == RemovalOption.LOGOUT

    yklocker.set_removal_option(RemovalOption.LOCK)
    assert yklocker.get_removal_option() == RemovalOption.LOCK

    yklocker.set_removal_option(RemovalOption.NOTHING)
    assert yklocker.get_removal_option() == RemovalOption.NOTHING


def test_yklock_getset_timeout():
    yklocker = YkLock()
    input = 15
    yklocker.set_timeout(input)
    yklocker.set_timeout("a")
    yklocker.set_timeout(-1)

    assert yklocker.get_timeout() == input


def test_yklock_lockLinux():
    # Test Linux lock
    platform.system = lambda: "Linux"
    linuxLocker = YkLock()
    with patch.object(os, "popen") as mock_popen:
        linuxLocker.lock()
        mock_popen.assert_called_once()
        assert "ScreenSaver.Lock" in mock_popen.call_args[0][0]


def test_yklock_logoutLinux():
    # Test Linux logout
    platform.system = lambda: "Linux"
    linuxLocker = YkLock()
    linuxLocker.set_removal_option(RemovalOption.LOGOUT)
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
    windowsLocker = YkLock()
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
    windowsLocker = YkLock()
    windowsLocker.set_removal_option(RemovalOption.LOGOUT)

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
    macLocker = YkLock()
    macLocker.lock()

    mock_CDLL.assert_called_once()


@patch("sciber_yklocker.servicemanager")
def test_yklock_logger_windows(m_servicemanager):
    platform.system = lambda: "Windows"
    winlocker = YkLock()
    with patch("sciber_yklocker.servicemanager.LogInfoMsg") as mock_log:
        winlocker.logger("testmessage")
        mock_log.assert_called_once_with("testmessage")


def test_yklock_logger():
    platform.system = lambda: "Linux"
    linuxLocker = YkLock()
    with patch("builtins.print") as mock_print:
        linuxLocker.logger("testmessage")
        mock_print.assert_called_once_with("testmessage")


@patch("sciber_yklocker.scan_devices", return_value=[0, 1])
def test_YkLock_is_yubikey_connected_false(_):
    platform.system = lambda: "Windows"
    winlocker = YkLock()

    # Patch logger to catch the message sent to it
    with patch("sciber_yklocker.YkLock.logger", MagicMock()) as mock_logger:
        # Make sure no YubiKeys are found by return an empty array
        with patch("sciber_yklocker.list_all_devices", lambda: []):
            assert winlocker.is_yubikey_connected() is False

        mock_logger.assert_not_called()


@patch("sciber_yklocker.scan_devices", return_value=[0, 1])
def test_YkLock_is_yubikey_connected_true(_):
    platform.system = lambda: "Windows"
    winlocker = YkLock()

    # Patch logger to catch the serial sent to it
    with patch("sciber_yklocker.YkLock.logger", MagicMock()) as mock_logger:
        # Make sure one "YubiKey" is found
        with patch("sciber_yklocker.list_all_devices", mock_list_one_device):
            assert winlocker.is_yubikey_connected() is True
        # Make sure we got the right serial
        assert "0123456789#" in mock_logger.call_args[0][0]


def test_reg_create_key():
    reg_reset()
    # Use fake registry
    with patch("sciber_yklocker.winreg", fake_winreg):
        create_key_handle = reg_create_key()

        # open key assumes the key has already been created
        open_key_handle = fake_winreg.OpenKey(fake_winreg.HKEY_LOCAL_MACHINE, REG_PATH)
        assert create_key_handle.handle.full_key == open_key_handle.handle.full_key
        fake_winreg.CloseKey(create_key_handle)
        fake_winreg.CloseKey(open_key_handle)


# Test non-existing registry
def test_reg_create_key_error():
    reg_reset()
    with patch("sciber_yklocker.winreg", None):
        assert reg_create_key() is False


def test_reg_query_key():
    reg_reset()
    # Use fake registry
    with patch("sciber_yklocker.winreg", fake_winreg):
        input = "1"
        key_handle = reg_create_key()
        reg_set_key(key_handle, REG_TIMEOUT, input)
        assert reg_query_key(key_handle, REG_TIMEOUT) is input
        fake_winreg.CloseKey(key_handle)


def test_reg_query_key_error():
    reg_reset()
    # Use fake registry
    with patch("sciber_yklocker.winreg", fake_winreg):
        key_handle = reg_create_key()
        # Non-existing key should return None
        assert reg_query_key(key_handle, "nada") is False
        fake_winreg.CloseKey(key_handle)


def test_reg_set_key():
    reg_reset()
    # Use fake registry
    with patch("sciber_yklocker.winreg", fake_winreg):
        key_handle = reg_create_key()
        # Successfully creating a key:value should return True
        ret = reg_set_key(key_handle, "name1", "value1")
        assert ret is True

        # Successfully querying that value should, return the value
        ret = reg_query_key(key_handle, "name1")
        assert ret == "value1"

        fake_winreg.CloseKey(key_handle)


def test_reg_set_key_error():
    reg_reset()
    # Use fake registry
    with patch("sciber_yklocker.winreg", fake_winreg):
        # "1" is an invalid key handle
        assert reg_set_key("1", "2", "3") is False


def test_reg_handler():
    # No real key handle to close so mock winreg
    with patch("sciber_yklocker.winreg", MagicMock()):
        # Our key handle
        with patch("sciber_yklocker.reg_create_key", lambda: True):
            # Assume no previous entries in the registry
            with patch("sciber_yklocker.reg_query_key", lambda a, b: False):
                # Mock successful key create
                with patch("sciber_yklocker.reg_set_key", MagicMock()) as mock_set:
                    assert reg_handler("a", "woo") == "woo"
                    mock_set.assert_called_once()


def test_reg_handler_error():
    # Our key handle is True
    with patch("sciber_yklocker.reg_create_key", lambda: False):
        assert reg_handler("a", "b") is False


def test_reg_check_timeout():
    yklocker = YkLock()
    # Assume the registry returns 15
    with patch("sciber_yklocker.reg_handler", lambda a, b: "15"):
        reg_check_timeout(yklocker)

    assert yklocker.get_timeout() == 15


def test_reg_check_timeout_error():
    yklocker = YkLock()
    # Check with another value than the default
    yklocker.set_timeout(15)
    with patch("sciber_yklocker.reg_handler", lambda a, b: False):
        reg_check_timeout(yklocker)

    assert yklocker.get_timeout() == 15


def test_reg_check_removal_option():
    yklocker = YkLock()
    # Assume the registry returns logout
    with patch("sciber_yklocker.reg_handler", lambda a, b: RemovalOption.LOGOUT):
        reg_check_removal_option(yklocker)

    assert yklocker.get_removal_option() == RemovalOption.LOGOUT


def test_reg_check_removal_option_error():
    yklocker = YkLock()
    # Check with another value than the default
    yklocker.set_removal_option(RemovalOption.LOGOUT)
    with patch("sciber_yklocker.reg_handler", lambda a, b: False):
        reg_check_removal_option(yklocker)

    assert yklocker.get_removal_option() == RemovalOption.LOGOUT


def test_reg_check_updates_no_update():
    yklocker = YkLock()

    # No updates just return the default values
    with patch("sciber_yklocker.reg_check_timeout", lambda a: yklocker.get_timeout()):
        with patch(
            "sciber_yklocker.reg_check_removal_option",
            lambda a: yklocker.get_removal_option(),
        ):
            with patch("sciber_yklocker.YkLock.logger", MagicMock()) as mock_logger:
                reg_check_updates(yklocker)
                # Logger should not have been called. No new values.
                mock_logger.assert_not_called()


def test_reg_check_updates_with_update():
    yklocker = YkLock()

    # Updates from registy are non-default values:
    with patch("sciber_yklocker.reg_check_timeout", lambda a: 15):
        with patch(
            "sciber_yklocker.reg_check_removal_option", lambda a: RemovalOption.LOGOUT
        ):
            with patch("sciber_yklocker.YkLock.logger", MagicMock()) as mock_logger:
                reg_check_updates(yklocker)
                # Logger should not have been called. No new values.
                mock_logger.assert_called_once()


@patch.object(YkLock, "lock")
@patch("sciber_yklocker.servicemanager")
# Make sure we trigger the service interruption to quit the loop
def test_loop_code_no_yubikey_windows(m_servicemanager, mock_lock):
    platform.system = lambda: "Windows"
    winlocker = YkLock()
    # Patch sleep and connection
    winlocker.get_timeout = lambda: 0
    winlocker.is_yubikey_connected = lambda: False

    # Mock win32event constant and function
    mock_win32event = win32event
    mock_win32event.WAIT_OBJECT_0 = 0
    mock_win32event.WaitForSingleObject = lambda a, b: 0

    # Patch logger to catch messages
    with patch("sciber_yklocker.YkLock.logger", MagicMock()) as mock_logger:
        loop_code(MagicMock(), winlocker)

        # Make sure we got the right message
        mock_logger.assert_called_with("YubiKey Disconnected. Locking workstation")

    # Make sure lock was called, no arguments expected
    mock_lock.assert_called_once_with()


@patch.object(YkLock, "lock")
@patch("sciber_yklocker.servicemanager")
# Make sure we trigger the service interruption to quit the loop
def test_loop_code_with_yubikey_windows(m_servicemanager, mock_lock):
    platform.system = lambda: "Windows"
    winlocker = YkLock()
    # Patch sleep and connection
    winlocker.get_timeout = lambda: 0
    winlocker.is_yubikey_connected = lambda: True

    # Mock win32event constant and function
    mock_win32event = win32event
    mock_win32event.WAIT_OBJECT_0 = 0
    mock_win32event.WaitForSingleObject = lambda a, b: 0

    # Patch logger to catch messages
    with patch("sciber_yklocker.YkLock.logger", MagicMock()):
        loop_code(MagicMock(), winlocker)
    # Make sure lock was not called
    mock_lock.assert_not_called()


def test_init_yklocker():
    platform.system = lambda: "Windows"
    # Call the function with non-default settings and verify them
    with patch(
        "sciber_yklocker.reg_check_timeout", MagicMock()
    ) as mock_reg_check_timeout:
        with patch(
            "sciber_yklocker.reg_check_removal_option", MagicMock()
        ) as mock_reg_check_removal_option:
            yklocker = init_yklocker(RemovalOption.LOGOUT, 15)

            # Make sure gets were called but dont enter the functions
            mock_reg_check_removal_option.assert_called_once()
            mock_reg_check_timeout.assert_called_once()

    assert yklocker.get_removal_option() == RemovalOption.LOGOUT
    assert yklocker.get_timeout() == 15


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
    with patch("sciber_yklocker.loop_code", MagicMock()) as mock_loop_code:
        with patch("sciber_yklocker.init_yklocker", MagicMock()) as mock_init_yklocker:
            mock_servicemanager = servicemanager
            mock_servicemanager.LogMsg = MagicMock()
            mock_servicemanager.PYS_SERVICE_STARTED = 0
            mock_servicemanager.EVENTLOG_INFORMATION_TYPE = 0

            # Call the function
            win_service.SvcDoRun()
            mock_servicemanager.LogMsg.assert_called_once()
            mock_init_yklocker.assert_called_once()
            mock_loop_code.assert_called_once()


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
    with patch("sciber_yklocker.loop_code", MagicMock()) as mock_loop_code:
        with patch("sciber_yklocker.init_yklocker", MagicMock()) as mock_init_yklocker:
            main([""])
            mock_loop_code.assert_called_once()
            mock_init_yklocker.assert_called_once()


def test_main_with_logout():
    platform.system = lambda: "Linux"
    # Dont go inte the loop but make sure it was called
    with patch("sciber_yklocker.loop_code", MagicMock()) as mock_loop_code:
        with patch("sciber_yklocker.init_yklocker", MagicMock()) as mock_init_yklocker:
            main(["-l", "Logout", "-t", "5"])
            mock_loop_code.assert_called_once()
            mock_init_yklocker.assert_called_once_with(RemovalOption.LOGOUT, 5)


def test_main_with_args():
    platform.system = lambda: "Linux"
    # Dont go inte the loop but make sure it was called
    with patch("sciber_yklocker.loop_code", MagicMock()) as mock_loop_code:
        with patch("sciber_yklocker.init_yklocker", MagicMock()) as mock_init_yklocker:
            main(["-l", "doNothing", "-t", "5"])
            mock_loop_code.assert_called_once()
            mock_init_yklocker.assert_called_once_with(RemovalOption.NOTHING, 5)
