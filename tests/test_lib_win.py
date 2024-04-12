import platform

from sciber_yklocker.models.myos import MyOS

if platform.system() == MyOS.WIN:
    from unittest.mock import MagicMock, patch
    import fake_winreg

    from sciber_yklocker.lib.win import (
        REG_PATH,
        REG_REMOVALOPTION,
        REG_TIMEOUT,
        AppServerSvc,
        check_service_interruption,
        reg_check_removal_option,
        reg_check_timeout,
        reg_check_updates,
        reg_query_key,
        lock_system,
        log_message,
        servicemanager,
        socket,
        win32event,
        win32service,
        win_main,
    )
    from sciber_yklocker.models.removaloption import RemovalOption
    from sciber_yklocker.models.yklock import YkLock

    #### Test functions ####

    @patch("sciber_yklocker.lib.win.servicemanager")
    def test_log_message(m_servicemanager) -> None:
        m_servicemanager.LogInfoMsg = MagicMock()

        log_message("testmessage")
        m_servicemanager.LogInfoMsg.assert_called_once_with("testmessage")

    @patch("sciber_yklocker.lib.win.win32con")
    @patch("sciber_yklocker.lib.win.win32ts")
    @patch("sciber_yklocker.lib.win.win32process")
    @patch("sciber_yklocker.lib.win.win32profile")
    def test_lock_system_lock(
        m_win32profile, m_win32process, m_win32ts, m_win32con
    ) -> None:
        m_win32con.NORMAL_PRIORITY_CLASS = 0
        m_win32ts.WTSQueryUserToken = MagicMock()
        m_win32profile.CreateEnvironmentBlock = MagicMock()
        m_win32process.CreateProcessAsUser = MagicMock(return_value=[0, 1, 2, 3])

        # Test Windows LOCK
        lock_system(RemovalOption.LOCK)

        m_win32process.CreateProcessAsUser.assert_called_once()
        assert "LockWorkStation" in m_win32process.CreateProcessAsUser.call_args[0][2]

    @patch("sciber_yklocker.lib.win.win32con")
    @patch("sciber_yklocker.lib.win.win32ts")
    @patch("sciber_yklocker.lib.win.win32process")
    @patch("sciber_yklocker.lib.win.win32profile")
    def test_lock_system_logout(
        m_win32profile, m_win32process, m_win32ts, m_win32con
    ) -> None:
        m_win32con.NORMAL_PRIORITY_CLASS = 0
        m_win32ts.WTSQueryUserToken = MagicMock()
        m_win32profile.CreateEnvironmentBlock = MagicMock()
        m_win32process.CreateProcessAsUser = MagicMock(return_value=[0, 1, 2, 3])

        # Test Windows LOGOUT
        lock_system(RemovalOption.LOGOUT)

        m_win32process.CreateProcessAsUser.assert_called_once()
        assert (
            "logoff.exe" in m_win32process.CreateProcessAsUser.call_args_list[0][0][2]
        )

    def test_check_service_interruption_true() -> None:
        # Mock win32event constant and function
        mock_win32event = win32event
        mock_win32event.WAIT_OBJECT_0 = 1
        mock_win32event.WaitForSingleObject = MagicMock(return_value=0)

        # MagicMock the serviceObject
        # Expect WaitForSingleObject to have been called
        # Expet the return to be True == continue looping
        assert check_service_interruption(MagicMock()) is True
        mock_win32event.WaitForSingleObject.assert_called_once()

    def test_check_service_interruption_false() -> None:
        # Mock win32event constant and function
        mock_win32event = win32event
        mock_win32event.WAIT_OBJECT_0 = 1
        mock_win32event.WaitForSingleObject = MagicMock(return_value=1)

        # MagicMock the serviceObject
        # Expect WaitForSingleObject to have been called
        # Expet the return to be False == stop looping
        assert check_service_interruption(MagicMock()) is False
        mock_win32event.WaitForSingleObject.assert_called_once()

    def test_reg_query_key_empty() -> None:
        # Use fake registry
        with patch("sciber_yklocker.lib.win.winreg", fake_winreg):
            with patch("sciber_yklocker.lib.win.log_message", MagicMock()) as m:
                # Empty registry should return False
                assert reg_query_key(REG_REMOVALOPTION) is False
                assert reg_query_key(REG_TIMEOUT) is False
                assert "Error when attempting to read the registry" in m.call_args[0][0]

    def test_reg_query_key_with_values() -> None:
        # Use fake registry - with values
        key_handle = fake_winreg.CreateKey(fake_winreg.HKEY_LOCAL_MACHINE, REG_PATH)
        fake_winreg.SetValueEx(
            key_handle,
            REG_REMOVALOPTION,
            0,
            fake_winreg.REG_SZ,
            str(RemovalOption.LOCK),
        )
        fake_winreg.SetValueEx(key_handle, REG_TIMEOUT, 0, fake_winreg.REG_DWORD, 22)
        key_handle.Close()

        with patch("sciber_yklocker.lib.win.winreg", fake_winreg):
            assert reg_query_key(REG_REMOVALOPTION) == RemovalOption.LOCK
            assert int(reg_query_key(REG_TIMEOUT)) == 22

        # Cleanup: Delete our values
        key_handle = fake_winreg.OpenKey(fake_winreg.HKEY_LOCAL_MACHINE, REG_PATH)
        fake_winreg.DeleteValue(key_handle, REG_REMOVALOPTION)
        fake_winreg.DeleteValue(key_handle, REG_TIMEOUT)
        fake_winreg.CloseKey(key_handle)
        key_handle.Close()

    def test_reg_check_timeout() -> None:
        yklocker = YkLock()
        # Assume the registry returns 15
        with patch("sciber_yklocker.lib.win.reg_query_key", lambda a: "15"):
            reg_check_timeout(yklocker)

        assert yklocker.get_timeout() == 15

    def test_reg_check_timeout_error() -> None:
        yklocker = YkLock()
        # Check with another value than the default
        yklocker.set_timeout(15)
        with patch("sciber_yklocker.lib.win.reg_query_key", lambda a: False):
            reg_check_timeout(yklocker)

        assert yklocker.get_timeout() == 15

    def test_reg_check_removal_option() -> None:
        yklocker = YkLock()
        # Assume the registry returns logout
        with patch(
            "sciber_yklocker.lib.win.reg_query_key", lambda a: RemovalOption.LOGOUT
        ):
            reg_check_removal_option(yklocker)

        assert yklocker.get_removal_option() == RemovalOption.LOGOUT

    def test_reg_check_removal_option_error() -> None:
        yklocker = YkLock()
        # Check with another value than the default
        with patch("sciber_yklocker.lib.win.reg_query_key", lambda a: False):
            reg_check_removal_option(yklocker)

        # IF no registry then it should be doNothing
        assert yklocker.get_removal_option() == RemovalOption.NOTHING

    def test_reg_check_updates_no_update() -> None:
        yklocker = YkLock()

        # No updates just return the default values
        with patch(
            "sciber_yklocker.lib.win.reg_check_timeout",
            lambda a: yklocker.get_timeout(),
        ):
            with patch(
                "sciber_yklocker.lib.win.reg_check_removal_option",
                lambda a: yklocker.get_removal_option(),
            ):
                with patch(
                    "sciber_yklocker.main.YkLock.logger", MagicMock()
                ) as mock_logger:
                    reg_check_updates(yklocker)
                    # Logger should not have been called. No new values.
                    mock_logger.assert_not_called()

    def test_reg_check_updates_with_update() -> None:
        yklocker = YkLock()

        # Updates from registy are non-default values:
        with patch("sciber_yklocker.lib.win.reg_check_timeout", lambda a: 15):
            with patch(
                "sciber_yklocker.lib.win.reg_check_removal_option",
                lambda a: RemovalOption.LOGOUT,
            ):
                with patch(
                    "sciber_yklocker.main.YkLock.logger", MagicMock()
                ) as mock_logger:
                    reg_check_updates(yklocker)
                    # Logger should not have been called. No new values.
                    mock_logger.assert_called_once()

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

    def AppServerSvc_SvcDoRun(win_service) -> None:
        # Dont go inte the loop but make sure it was called
        with patch("sciber_yklocker.main.loop_code", MagicMock()) as mock_loop_code:
            with patch(
                "sciber_yklocker.main.init_yklocker", MagicMock()
            ) as mock_init_yklocker:
                mock_servicemanager = servicemanager
                mock_servicemanager.LogMsg = MagicMock()
                mock_servicemanager.PYS_SERVICE_STARTED = 0
                mock_servicemanager.EVENTLOG_INFORMATION_TYPE = 0

                # Call the function
                win_service.SvcDoRun()
                mock_servicemanager.LogMsg.assert_called_once()
                mock_init_yklocker.assert_called_once()
                mock_loop_code.assert_called_once()

    def AppServerSvc_SvcStop(win_service) -> None:
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

    def test_AppServerSvc() -> None:
        win_service = AppServerSvc__init__()
        AppServerSvc_SvcDoRun(win_service)
        AppServerSvc_SvcStop(win_service)

    @patch("sciber_yklocker.lib.win.servicemanager")
    def test_win_main(m_servicemanager) -> None:
        m_servicemanager.StartServiceCtrlDispatcher = MagicMock()
        m_servicemanager.PrepareToHostSingle = MagicMock()
        m_servicemanager.Initialize = MagicMock()
        win_main()

        # Make sure the code calls these:
        m_servicemanager.Initialize.assert_called_once_with()
        m_servicemanager.PrepareToHostSingle.assert_called_once()
        m_servicemanager.StartServiceCtrlDispatcher.assert_called_once()

    @patch("sciber_yklocker.lib.win.servicemanager")
    def test_main_win_error(m_servicemanager) -> None:
        m_servicemanager.StartServiceCtrlDispatcher = MagicMock()
        m_servicemanager.PrepareToHostSingle = MagicMock()
        m_servicemanager.Initialize = MagicMock()

        m_servicemanager.StartServiceCtrlDispatcher.side_effect = SystemError
        with patch("builtins.print") as mock_print:
            win_main()
            # If we catch the error we should see prints
            mock_print.assert_called()
        # Make sure the code calls these:
        m_servicemanager.Initialize.assert_called_once_with()
        m_servicemanager.PrepareToHostSingle.assert_called_once()
        m_servicemanager.StartServiceCtrlDispatcher.assert_called_once()
