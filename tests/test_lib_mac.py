import platform

from sciber_yklocker.lib import MyOS

if platform.system() == MyOS.MAC:
    from unittest.mock import MagicMock, patch

    from sciber_yklocker.lib import MyOS, RemovalOption
    from sciber_yklocker.lib_mac import lock_system, log_message

    @patch("sciber_yklocker.lib_mac.CDLL")
    def test_lock_system(mock_CDLL) -> None:
        lock_system(RemovalOption.LOCK)
        mock_CDLL.assert_called_once()

    def test_log_message() -> None:
        with patch("sciber_yklocker.lib_mac.os_log", MagicMock()) as mock_print:
            log_message("testmessage")
            mock_print.assert_called_once()
            assert "testmessage" in mock_print.call_args[0]
