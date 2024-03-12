import platform
from unittest.mock import MagicMock, patch

from sciber_yklocker.lib import MyOS, RemovalOption
from sciber_yklocker.main import YkLock, init_yklocker, loop_code, main

##### Helper Functions ######


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
def mock_continue_looping() -> bool:
    global temp_counter
    if temp_counter == 0:
        temp_counter += 1
        return True
    else:
        return False


#####################################

##### Test Functions ######


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
    with patch("sciber_yklocker.main.lock_system", MagicMock()) as mock_lock_system:
        yklocker = YkLock()
        yklocker.lock()
    mock_lock_system.assert_not_called()


def test_yklock_lock_lock() -> None:
    with patch("sciber_yklocker.main.lock_system", MagicMock()) as mock_lock_system:
        yklocker = YkLock()
        yklocker.set_removal_option(RemovalOption.LOCK)
        yklocker.lock()
    mock_lock_system.assert_called_once()


def test_yklock_logger() -> None:
    with patch("sciber_yklocker.main.log_message", MagicMock()) as mock_log_message:
        yklocker = YkLock()
        yklocker.logger("test message 1")

    mock_log_message.assert_called_once_with("test message 1")


def test_YkLock_is_yubikey_connected_false() -> None:
    yklocker = YkLock()
    # Make sure no YubiKeys are found by return an empty array
    with patch("sciber_yklocker.main.list_all_devices", lambda: []):
        assert yklocker.is_yubikey_connected() is False


def test_YkLock_is_yubikey_connected_true() -> None:
    yklocker = YkLock()

    # Make sure one "YubiKey" is found
    with patch("sciber_yklocker.main.list_all_devices", mock_list_one_device):
        assert yklocker.is_yubikey_connected() is True


def test_YkLock_continue_looping_true() -> None:
    yklocker = YkLock()
    if platform.system() == MyOS.WIN:
        with patch(
            "sciber_yklocker.main.check_service_interruption",
            MagicMock(return_value=True),
        ) as mock_check_service_interruption:
            # MagicMock the serviceObject
            # Expect the return to be True == continue looping
            assert yklocker.continue_looping() is True

            mock_check_service_interruption.assert_called_once()

    else:
        assert yklocker.continue_looping(MagicMock()) is True


def test_loop_code_no_yubikey() -> None:
    yklocker = YkLock()

    # Patch sleep and connection
    yklocker.get_timeout = lambda: 0
    yklocker.is_yubikey_connected = lambda: False

    # Get the global counter and set it to zero
    global temp_counter
    temp_counter = 0

    # Patch continue_looping to enter while-loop only once
    with patch(
        "sciber_yklocker.main.YkLock.continue_looping", MagicMock()
    ) as mock_loop:
        mock_loop.side_effect = mock_continue_looping
        # Skip registry updates
        with patch("platform.system", MagicMock(return_value=MyOS.LX)):
            # Dont actually lock the device during tests
            with patch("sciber_yklocker.main.YkLock.lock", MagicMock()) as mock_lock:
                # Patch logger to catch messages
                with patch(
                    "sciber_yklocker.main.YkLock.logger", MagicMock()
                ) as mock_logger:
                    loop_code(yklocker)

                    # Make sure we got the right message
                    mock_logger.assert_called_with(
                        "YubiKey not found, action to take: doNothing"
                    )

                # Make sure lock was called, no arguments expected
                mock_lock.assert_called_once_with()


def test_loop_code_with_yubikey() -> None:
    yklocker = YkLock()
    # Patch sleep and connection
    yklocker.get_timeout = lambda: 0
    yklocker.is_yubikey_connected = lambda: True

    # Get the global counter and set it to zero
    global temp_counter
    temp_counter = 0

    # Patch continue_looping to enter while-loop only once
    with patch(
        "sciber_yklocker.main.YkLock.continue_looping", MagicMock()
    ) as mock_loop:
        mock_loop.side_effect = mock_continue_looping
        # Skip registry updates
        with patch("platform.system", MagicMock(return_value=MyOS.LX)):
            # Dont actually lock the device during tests
            with patch("sciber_yklocker.main.YkLock.lock", MagicMock()) as mock_lock:
                # Patch logger to catch messages
                with patch("sciber_yklocker.main.YkLock.logger", MagicMock()):
                    loop_code(yklocker)
                # Make sure lock was not called
                mock_lock.assert_not_called()


def test_init_yklocker_win() -> None:
    if platform.system() == MyOS.WIN:
        # Call the function with non-default settings and verify them
        with patch(
            "sciber_yklocker.main.reg_check_timeout", MagicMock()
        ) as mock_reg_check_timeout:
            with patch(
                "sciber_yklocker.main.reg_check_removal_option", MagicMock()
            ) as mock_reg_check_removal_option:
                yklocker = init_yklocker(RemovalOption.LOGOUT, 15)

                # Make sure gets were called but dont enter the functions
                mock_reg_check_removal_option.assert_called_once()
                mock_reg_check_timeout.assert_called_once()

        assert yklocker.get_removal_option() == RemovalOption.LOGOUT
        assert yklocker.get_timeout() == 15


def test_init_yklocker_lx() -> None:
    if platform.system() == MyOS.LX or platform.system() == MyOS.MAC:
        yklocker = init_yklocker(RemovalOption.LOGOUT, 15)
        assert yklocker.get_removal_option() == RemovalOption.LOGOUT
        assert yklocker.get_timeout() == 15


def test_main_no_args() -> None:
    # Make sure we go into the argument checks
    with patch("platform.system", MagicMock(return_value=MyOS.LX)):
        # Dont go inte the loop but make sure it was called
        with patch("sciber_yklocker.main.loop_code", MagicMock()) as mock_loop_code:
            with patch(
                "sciber_yklocker.main.init_yklocker", MagicMock()
            ) as mock_init_yklocker:
                main([""])
                mock_init_yklocker.assert_called_once_with(None, None)
                mock_loop_code.assert_called_once()


def test_main_with_logout() -> None:
    # Make sure we go into the argument checks
    with patch("platform.system", MagicMock(return_value=MyOS.LX)):
        # Dont go inte the loop but make sure it was called
        with patch("sciber_yklocker.main.loop_code", MagicMock()) as mock_loop_code:
            with patch(
                "sciber_yklocker.main.init_yklocker", MagicMock()
            ) as mock_init_yklocker:
                main(["-l", "Logout", "-t", "5"])
                mock_loop_code.assert_called_once()
                mock_init_yklocker.assert_called_once_with(RemovalOption.LOGOUT, 5)


def test_main_with_doNothing() -> None:
    # Make sure we go into the argument checks
    with patch("platform.system", MagicMock(return_value=MyOS.LX)):
        # Dont go inte the loop but make sure it was called
        with patch("sciber_yklocker.main.loop_code", MagicMock()) as mock_loop_code:
            with patch(
                "sciber_yklocker.main.init_yklocker", MagicMock()
            ) as mock_init_yklocker:
                main(["-l", "doNothing", "-t", "5"])
                mock_loop_code.assert_called_once()
                mock_init_yklocker.assert_called_once_with(RemovalOption.NOTHING, 5)


def test_main_with_lock() -> None:
    # Make sure we go into the argument checks
    with patch("platform.system", MagicMock(return_value=MyOS.LX)):
        # Dont go inte the loop but make sure it was called
        with patch("sciber_yklocker.main.loop_code", MagicMock()) as mock_loop_code:
            with patch(
                "sciber_yklocker.main.init_yklocker", MagicMock()
            ) as mock_init_yklocker:
                main(["-l", "Lock", "-t", "5"])
                mock_loop_code.assert_called_once()
                mock_init_yklocker.assert_called_once_with(RemovalOption.LOCK, 5)
