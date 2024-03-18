from unittest.mock import MagicMock, patch

from sciber_yklocker.models.removaloption import RemovalOption
from sciber_yklocker.models.yklock import YkLock


def mock_list_one_device():
    class info:
        serial = "0123456789#"

    mydict = {"A": "devices", "B": info}
    devices = []
    devices.append(mydict.values())

    return devices


###########################################


def test_yklock_getset_timeout() -> None:
    yklocker = YkLock()
    input = 15
    yklocker.set_timeout(input)
    yklocker.set_timeout("a")
    yklocker.set_timeout(-1)

    assert yklocker.get_timeout() == input


def test_yklock_getset_removal_option() -> None:
    yklocker = YkLock()
    yklocker.set_removal_option(RemovalOption.LOGOUT)
    yklocker.set_removal_option("hello")
    assert yklocker.get_removal_option() == RemovalOption.LOGOUT

    yklocker.set_removal_option(RemovalOption.LOCK)
    assert yklocker.get_removal_option() == RemovalOption.LOCK

    yklocker.set_removal_option(RemovalOption.NOTHING)
    assert yklocker.get_removal_option() == RemovalOption.NOTHING


def test_yklock_lock_default() -> None:
    with patch(
        "sciber_yklocker.models.yklock.lock_system", MagicMock()
    ) as mock_lock_system:
        yklocker = YkLock()
        yklocker.lock()
    mock_lock_system.assert_not_called()


def test_yklock_lock_lock() -> None:
    with patch(
        "sciber_yklocker.models.yklock.lock_system", MagicMock()
    ) as mock_lock_system:
        yklocker = YkLock()
        yklocker.set_removal_option(RemovalOption.LOCK)
        yklocker.lock()
    mock_lock_system.assert_called_once()


def test_yklock_logger() -> None:
    with patch(
        "sciber_yklocker.models.yklock.log_message", MagicMock()
    ) as mock_log_message:
        yklocker = YkLock()
        yklocker.logger("test message 1")

    mock_log_message.assert_called_once_with("test message 1")


def test_YkLock_is_yubikey_connected_false() -> None:
    yklocker = YkLock()
    # Make sure no YubiKeys are found by return an empty array
    with patch("sciber_yklocker.models.yklock.list_all_devices", lambda: []):
        assert yklocker.is_yubikey_connected() is False


def test_YkLock_is_yubikey_connected_true() -> None:
    yklocker = YkLock()

    # Make sure one "YubiKey" is found
    with patch("sciber_yklocker.models.yklock.list_all_devices", mock_list_one_device):
        assert yklocker.is_yubikey_connected() is True
