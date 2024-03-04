import platform

if platform.system() == "Darwin":
    from unittest.mock import patch

    from lib import RemovalOption
    from sciber_yklocker import YkLock

    @patch("lib_mac.CDLL")
    def test_yklock_lockMac(mock_CDLL):
        # Test Mac Lock
        # platform.system = lambda: "Darwin"
        macLocker = YkLock()
        macLocker.set_removal_option(RemovalOption.LOCK)
        macLocker.lock()

        mock_CDLL.assert_called_once()
