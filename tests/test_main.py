import platform
from unittest.mock import MagicMock, patch

from sciber_yklocker.main import (
    continue_looping,
    init_yklocker,
    loop_code,
    main,
    check_arguments,
)
from sciber_yklocker.models.myos import MyOS
from sciber_yklocker.models.removaloption import RemovalOption
from sciber_yklocker.models.yklock import YkLock

##### Helper Functions ######


# global counter
temp_counter = 0


# Get the mock_continue_looping function to first return True then False
def mock_continue_looping(yklocker: YkLock) -> bool:
    global temp_counter
    if temp_counter == 0:
        temp_counter += 1
        return True
    else:
        return False


#####################################

##### Test Functions ######


def test_continue_looping_true() -> None:
    yklocker = YkLock()
    if platform.system() == MyOS.WIN:
        with patch(
            "sciber_yklocker.main.check_service_interruption",
            MagicMock(return_value=True),
        ) as mock_check_service_interruption:
            # MagicMock the serviceObject
            # Expect the return to be True == continue looping
            assert continue_looping(yklocker) is True

            mock_check_service_interruption.assert_called_once()

    else:
        assert continue_looping(yklocker) is True


def test_loop_code_no_yubikey() -> None:
    yklocker = YkLock()

    # Patch sleep and connection
    yklocker.get_timeout = lambda: 0
    yklocker.is_yubikey_connected = lambda: False

    # Get the global counter and set it to zero
    global temp_counter
    temp_counter = 0

    # Patch continue_looping to enter while-loop only once
    with patch("sciber_yklocker.main.continue_looping", MagicMock()) as mock_loop:
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
    with patch("sciber_yklocker.main.continue_looping", MagicMock()) as mock_loop:
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


def test_check_arguments_no_args() -> None:
    with patch("sys.argv", ["yklocker.exe"]):
        assert RemovalOption.NOTHING, 10 == check_arguments()


def test_check_arguments_with_logout() -> None:
    with patch("sys.argv", ["yklocker.exe", "-l", "Logout", "-t", "5"]):
        assert RemovalOption.LOGOUT, 5 == check_arguments()


def test_check_arguments_with_doNothing() -> None:
    with patch("sys.argv", ["yklocker.exe", "-l", "doNothing", "-t", "5"]):
        assert RemovalOption.NOTHING, 5 == check_arguments()


def test_check_arguments_with_lock() -> None:
    with patch("sys.argv", ["yklocker.exe", "-l", "Lock", "-t", "5"]):
        assert RemovalOption.LOCK, 5 == check_arguments()
