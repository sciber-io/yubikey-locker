import platform

if platform.system() == "Darwin":
    from unittest.mock import MagicMock, patch

    from sciber_yklocker.lib import RemovalOption
    from sciber_yklocker.lib_mac import lock_system, log_message

    @patch("sciber_yklocker.lib_mac.CDLL")
    def test_lock_system(mock_CDLL):
        lock_system(RemovalOption.LOCK)
        mock_CDLL.assert_called_once()

    def test_log_message():
        with patch("sciber_yklocker.lib_mac.syslog", MagicMock()) as mock_print:
            log_message("testmessage")
            mock_print.syslog.assert_called_once()
            assert "testmessage" in mock_print.syslog.call_args[0]
