import platform

from sciber_yklocker.lib import MyOS

if platform.system() == MyOS.LX:
    from unittest.mock import MagicMock, patch

    from sciber_yklocker.lib import RemovalOption
    from sciber_yklocker.lib_lx import lock_system, log_message, os

    def test_lock_system_lock() -> None:
        # Test Linux lock
        with patch.object(os, "popen") as mock_popen:
            lock_system(RemovalOption.LOCK)
            mock_popen.assert_called_once()
            assert "ScreenSaver.Lock" in mock_popen.call_args[0][0]

    def test_lock_system_logout() -> None:
        # Test Linux logout
        with patch.object(os, "popen") as mock_popen:
            lock_system(RemovalOption.LOGOUT)
            mock_popen.assert_called_once()
            assert "SessionManager.Logout" in mock_popen.call_args[0][0]

    def test_log_message() -> None:
        with patch("sciber_yklocker.lib_lx.syslog", MagicMock()) as mock_print:
            log_message("testmessage")
            mock_print.syslog.assert_called_once()
            assert "testmessage" in mock_print.syslog.call_args[0]
