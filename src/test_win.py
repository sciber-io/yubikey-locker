from unittest.mock import MagicMock, patch

import fake_winreg

from lib import RemovalOption
from sciber_yklocker import YkLock, init_yklocker, loop_code, main, platform

if platform.system() == "Windows":
    from lib_win import (
        REG_PATH,
        REG_REMOVALOPTION,
        REG_TIMEOUT,
        AppServerSvc,
        reg_check_removal_option,
        reg_check_timeout,
        reg_check_updates,
        reg_query_key,
        servicemanager,
        socket,
        win32event,
        win32service,
    )

    ### Helper Functions ##


def mock_list_one_device():
    class info:
        serial = "0123456789#"

    mydict = {"A": "devices", "B": info}
    devices = []
    devices.append(mydict.values())

    return devices


# global counter
temp_counter = 0


# Get the mock_continue_looping function to first return True then False
def mock_continue_looping(a):
    global temp_counter
    if temp_counter == 0:
        temp_counter += 1
        return True
    elif temp_counter > 0:
        return False


@patch("lib_win.win32con")
@patch("lib_win.win32ts")
@patch("lib_win.win32process")
@patch("lib_win.win32profile")
def test_yklock_lockWindows(m_win32profile, m_win32process, m_win32ts, m_win32con):
    windowsLocker = YkLock()
    windowsLocker.set_removal_option(RemovalOption.LOCK)
    m_win32con.NORMAL_PRIORITY_CLASS = 0
    m_win32ts.WTSQueryUserToken = MagicMock()
    m_win32profile.CreateEnvironmentBlock = MagicMock()
    m_win32process.CreateProcessAsUser = MagicMock(return_value=[0, 1, 2, 3])

    # Test Windows LOCK
    windowsLocker.lock()
    m_win32process.CreateProcessAsUser.assert_called_once()
    assert "LockWorkStation" in m_win32process.CreateProcessAsUser.call_args[0][2]


@patch("lib_win.win32con")
@patch("lib_win.win32ts")
@patch("lib_win.win32process")
@patch("lib_win.win32profile")
def test_yklock_logoutWindows(m_win32profile, m_win32process, m_win32ts, m_win32con):
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


@patch("lib_win.servicemanager")
def test_yklock_logger_windows(m_servicemanager):
    m_servicemanager.LogInfoMsg = MagicMock()

    platform.system = lambda: "Windows"
    winlocker = YkLock()
    winlocker.logger("testmessage")
    m_servicemanager.LogInfoMsg.assert_called_once_with("testmessage")


# @patch("sciber_yklocker.scan_devices", return_value=[0, 1])
def test_YkLock_is_yubikey_connected_false():
    winlocker = YkLock()

    # Patch logger to catch the message sent to it
    with patch("sciber_yklocker.YkLock.logger", MagicMock()) as mock_logger:
        # Make sure no YubiKeys are found by return an empty array
        with patch("sciber_yklocker.list_all_devices", lambda: []):
            assert winlocker.is_yubikey_connected() is False

        mock_logger.assert_not_called()


# @patch("sciber_yklocker.scan_devices", return_value=[0, 1])
def test_YkLock_is_yubikey_connected_true():
    winlocker = YkLock()

    # Patch logger to catch the serial sent to it
    with patch("sciber_yklocker.YkLock.logger", MagicMock()):
        # Make sure one "YubiKey" is found
        with patch("sciber_yklocker.list_all_devices", mock_list_one_device):
            assert winlocker.is_yubikey_connected() is True
        # Make sure we got the right serial
        # assert "0123456789#" in mock_logger.call_args[0]


def test_YkLock_continue_looping_true():
    # Mock win32event constant and function
    mock_win32event = win32event
    mock_win32event.WAIT_OBJECT_0 = 1
    mock_win32event.WaitForSingleObject = MagicMock(return_value=0)

    platform.system = lambda: "Windows"
    winlocker = YkLock()

    # MagicMock the serviceObject
    # Expect WaitForSingleObject to have been called
    # Expet the return to be True == continue looping
    assert winlocker.continue_looping(MagicMock()) is True
    mock_win32event.WaitForSingleObject.assert_called_once()


def test_YkLock_continue_looping_false():
    # Mock win32event constant and function
    mock_win32event = win32event
    mock_win32event.WAIT_OBJECT_0 = 0
    mock_win32event.WaitForSingleObject = MagicMock(return_value=0)

    platform.system = lambda: "Windows"
    winlocker = YkLock()

    # MagicMock the serviceObject
    # Expect WaitForSingleObject to have been called
    # Expet the return to be false  == stop looping
    assert winlocker.continue_looping(MagicMock()) is False
    mock_win32event.WaitForSingleObject.assert_called_once()


def test_reg_query_key_empty():
    # Use fake registry
    with patch("lib_win.winreg", fake_winreg):
        # Empty registry should return False
        assert reg_query_key(REG_REMOVALOPTION) is False
        assert reg_query_key(REG_TIMEOUT) is False


def test_reg_query_key_with_values():
    # Use fake registry - with values
    key_handle = fake_winreg.CreateKey(fake_winreg.HKEY_LOCAL_MACHINE, REG_PATH)
    fake_winreg.SetValueEx(
        key_handle, REG_REMOVALOPTION, 0, fake_winreg.REG_SZ, str(RemovalOption.LOCK)
    )
    fake_winreg.SetValueEx(key_handle, REG_TIMEOUT, 0, fake_winreg.REG_DWORD, 22)
    key_handle.Close()

    with patch("lib_win.winreg", fake_winreg):
        assert reg_query_key(REG_REMOVALOPTION) == RemovalOption.LOCK
        assert int(reg_query_key(REG_TIMEOUT)) == 22

    # Cleanup: Delete our values
    key_handle = fake_winreg.OpenKey(fake_winreg.HKEY_LOCAL_MACHINE, REG_PATH)
    fake_winreg.DeleteValue(key_handle, REG_REMOVALOPTION)
    fake_winreg.DeleteValue(key_handle, REG_TIMEOUT)
    fake_winreg.CloseKey(key_handle)
    key_handle.Close()


def test_reg_check_timeout():
    yklocker = YkLock()
    # Assume the registry returns 15
    with patch("lib_win.reg_query_key", lambda a: "15"):
        reg_check_timeout(yklocker)

    assert yklocker.get_timeout() == 15


def test_reg_check_timeout_error():
    yklocker = YkLock()
    # Check with another value than the default
    yklocker.set_timeout(15)
    with patch("lib_win.reg_query_key", lambda a: False):
        reg_check_timeout(yklocker)

    assert yklocker.get_timeout() == 15


def test_reg_check_removal_option():
    yklocker = YkLock()
    # Assume the registry returns logout
    with patch("lib_win.reg_query_key", lambda a: RemovalOption.LOGOUT):
        reg_check_removal_option(yklocker)

    assert yklocker.get_removal_option() == RemovalOption.LOGOUT


def test_reg_check_removal_option_error():
    yklocker = YkLock()
    # Check with another value than the default
    with patch("lib_win.reg_query_key", lambda a: False):
        reg_check_removal_option(yklocker)

    # IF no registry then it should be doNothing
    assert yklocker.get_removal_option() == RemovalOption.NOTHING


def test_reg_check_updates_no_update():
    yklocker = YkLock()

    # No updates just return the default values
    with patch("lib_win.reg_check_timeout", lambda a: yklocker.get_timeout()):
        with patch(
            "lib_win.reg_check_removal_option",
            lambda a: yklocker.get_removal_option(),
        ):
            with patch("sciber_yklocker.YkLock.logger", MagicMock()) as mock_logger:
                reg_check_updates(yklocker)
                # Logger should not have been called. No new values.
                mock_logger.assert_not_called()


def test_reg_check_updates_with_update():
    yklocker = YkLock()

    # Updates from registy are non-default values:
    with patch("lib_win.reg_check_timeout", lambda a: 15):
        with patch("lib_win.reg_check_removal_option", lambda a: RemovalOption.LOGOUT):
            with patch("sciber_yklocker.YkLock.logger", MagicMock()) as mock_logger:
                reg_check_updates(yklocker)
                # Logger should not have been called. No new values.
                mock_logger.assert_called_once()


def test_loop_code_no_yubikey_windows():
    winlocker = YkLock()

    # Patch sleep and connection
    winlocker.get_timeout = lambda: 0
    winlocker.is_yubikey_connected = lambda: False

    # Get the global counter and set it to zero
    global temp_counter
    temp_counter = 0

    # Patch continue_looping to enter while-loop only once
    with patch("sciber_yklocker.YkLock.continue_looping", MagicMock()) as mock_loop:
        mock_loop.side_effect = mock_continue_looping
        # Patch registry updates func
        with patch("sciber_yklocker.reg_check_updates", MagicMock()):
            # Dont actually lock the device during tests
            with patch("sciber_yklocker.YkLock.lock", MagicMock()) as mock_lock:
                # Patch logger to catch messages
                with patch("sciber_yklocker.YkLock.logger", MagicMock()) as mock_logger:
                    loop_code(MagicMock(), winlocker)

                    # Make sure we got the right message
                    mock_logger.assert_called_with(
                        "YubiKey not found. Locking workstation"
                    )

                # Make sure lock was called, no arguments expected
                mock_lock.assert_called_once_with()


def test_loop_code_with_yubikey_windows():
    winlocker = YkLock()
    # Patch sleep and connection
    winlocker.get_timeout = lambda: 0
    winlocker.is_yubikey_connected = lambda: True

    # Get the global counter and set it to zero
    global temp_counter
    temp_counter = 0

    # Patch continue_looping to enter while-loop only once
    with patch("sciber_yklocker.YkLock.continue_looping", MagicMock()) as mock_loop:
        mock_loop.side_effect = mock_continue_looping
        # Patch registry updates func
        with patch("sciber_yklocker.reg_check_updates", MagicMock()):
            # Dont actually lock the device during tests
            with patch("sciber_yklocker.YkLock.lock", MagicMock()) as mock_lock:
                # Patch logger to catch messages
                with patch("sciber_yklocker.YkLock.logger", MagicMock()):
                    loop_code(MagicMock(), winlocker)
                # Make sure lock was not called
                mock_lock.assert_not_called()


def test_init_yklocker():
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


@patch("lib_win.servicemanager")
def test_main_win(m_servicemanager):
    platform.system = lambda: "Windows"

    m_servicemanager.StartServiceCtrlDispatcher = MagicMock()
    m_servicemanager.PrepareToHostSingle = MagicMock()
    m_servicemanager.Initialize = MagicMock()
    main("")

    # Make sure the code calls these:
    m_servicemanager.Initialize.assert_called_once_with()
    m_servicemanager.PrepareToHostSingle.assert_called_once()
    m_servicemanager.StartServiceCtrlDispatcher.assert_called_once()


@patch("lib_win.servicemanager")
def test_main_win_error(m_servicemanager):
    platform.system = lambda: "Windows"
    m_servicemanager.StartServiceCtrlDispatcher = MagicMock()
    m_servicemanager.PrepareToHostSingle = MagicMock()
    m_servicemanager.Initialize = MagicMock()

    m_servicemanager.StartServiceCtrlDispatcher.side_effect = SystemError
    with patch("builtins.print") as mock_print:
        main("")
        mock_print.assert_called_once()
    # Make sure the code calls these:
    m_servicemanager.Initialize.assert_called_once_with()
    m_servicemanager.PrepareToHostSingle.assert_called_once()
    m_servicemanager.StartServiceCtrlDispatcher.assert_called_once()
