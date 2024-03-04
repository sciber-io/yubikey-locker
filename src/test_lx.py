import platform

if platform.system() == "Linux":
    from unittest.mock import MagicMock, patch

    from lib import RemovalOption
    from lib_lx import os
    from sciber_yklocker import YkLock, main, platform

    def test_yklock_lockLinux():
        # Test Linux lock
        platform.system = lambda: "Linux"
        linuxLocker = YkLock()
        linuxLocker.set_removal_option(RemovalOption.LOCK)
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

    def test_yklock_logger():
        platform.system = lambda: "Linux"
        linuxLocker = YkLock()
        with patch("sciber_yklocker.syslog", MagicMock()) as mock_print:
            linuxLocker.logger("testmessage")
            mock_print.syslog.assert_called_once()
            assert "testmessage" in mock_print.syslog.call_args[0]

    def test_main_no_args():
        platform.system = lambda: "Linux"
        # Dont go inte the loop but make sure it was called
        with patch("sciber_yklocker.loop_code", MagicMock()) as mock_loop_code:
            with patch(
                "sciber_yklocker.init_yklocker", MagicMock()
            ) as mock_init_yklocker:
                main([""])
                mock_loop_code.assert_called_once()
                mock_init_yklocker.assert_called_once()

    def test_main_with_logout():
        platform.system = lambda: "Linux"
        # Dont go inte the loop but make sure it was called
        with patch("sciber_yklocker.loop_code", MagicMock()) as mock_loop_code:
            with patch(
                "sciber_yklocker.init_yklocker", MagicMock()
            ) as mock_init_yklocker:
                main(["-l", "Logout", "-t", "5"])
                mock_loop_code.assert_called_once()
                mock_init_yklocker.assert_called_once_with(RemovalOption.LOGOUT, 5)

    def test_main_with_args():
        platform.system = lambda: "Linux"
        # Dont go inte the loop but make sure it was called
        with patch("sciber_yklocker.loop_code", MagicMock()) as mock_loop_code:
            with patch(
                "sciber_yklocker.init_yklocker", MagicMock()
            ) as mock_init_yklocker:
                main(["-l", "doNothing", "-t", "5"])
                mock_loop_code.assert_called_once()
                mock_init_yklocker.assert_called_once_with(RemovalOption.NOTHING, 5)
