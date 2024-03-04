from unittest.mock import MagicMock, patch

from lib import MyPlatform, RemovalOption
from sciber_yklocker import (  # platform,
    YkLock,
    get_my_platform,
    init_yklocker,
    loop_code,
    main,
)

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
def mock_continue_looping(a):
    global temp_counter
    if temp_counter == 0:
        temp_counter += 1
        return True
    elif temp_counter > 0:
        return False


#####################################

##### Test Functions ######


def test_get_my_platform_unknown():
    with patch("sciber_yklocker.platform", MagicMock(return_value="nada")):
        assert get_my_platform() == MyPlatform.UNKNOWN


def test_yklock_getset_timeout():
    yklocker = YkLock()
    input = 15
    yklocker.set_timeout(input)
    yklocker.set_timeout("a")
    yklocker.set_timeout(-1)

    assert yklocker.get_timeout() == input


def test_yklock_getset_removal_option():
    yklocker = YkLock()
    yklocker.set_removal_option(RemovalOption.LOGOUT)
    yklocker.set_removal_option("hello")
    assert yklocker.get_removal_option() == RemovalOption.LOGOUT

    yklocker.set_removal_option(RemovalOption.LOCK)
    assert yklocker.get_removal_option() == RemovalOption.LOCK

    yklocker.set_removal_option(RemovalOption.NOTHING)
    assert yklocker.get_removal_option() == RemovalOption.NOTHING


def test_yklock_lock_default():
    with patch("sciber_yklocker.lock_system", MagicMock()) as mock_lock_system:
        yklocker = YkLock()
        yklocker.lock()
    mock_lock_system.assert_not_called()


def test_yklock_lock_lock():
    with patch("sciber_yklocker.lock_system", MagicMock()) as mock_lock_system:
        yklocker = YkLock()
        yklocker.set_removal_option(RemovalOption.LOCK)
        yklocker.lock()
    mock_lock_system.assert_called_once()


def test_yklock_logger():
    with patch("sciber_yklocker.log_message", MagicMock()) as mock_log_message:
        yklocker = YkLock()
        yklocker.logger("test message 1")

    mock_log_message.assert_called_once_with("test message 1")


def test_YkLock_is_yubikey_connected_false():
    yklocker = YkLock()
    # Make sure no YubiKeys are found by return an empty array
    with patch("sciber_yklocker.list_all_devices", lambda: []):
        assert yklocker.is_yubikey_connected() is False


def test_YkLock_is_yubikey_connected_true():
    yklocker = YkLock()

    # Make sure one "YubiKey" is found
    with patch("sciber_yklocker.list_all_devices", mock_list_one_device):
        assert yklocker.is_yubikey_connected() is True


def test_YkLock_continue_looping_true():
    yklocker = YkLock()
    if yklocker.MyPlatformversion == MyPlatform.WIN:
        with patch(
            "sciber_yklocker.check_service_interruption", MagicMock(return_value=True)
        ) as mock_check_service_interruption:
            # MagicMock the serviceObject
            # Expect the return to be True == continue looping
            assert yklocker.continue_looping(MagicMock()) is True

            mock_check_service_interruption.assert_called_once()

    else:
        assert yklocker.continue_looping(MagicMock()) is True


def test_loop_code_no_yubikey():
    yklocker = YkLock()

    # Patch sleep and connection
    yklocker.get_timeout = lambda: 0
    yklocker.is_yubikey_connected = lambda: False

    # Get the global counter and set it to zero
    global temp_counter
    temp_counter = 0

    # Patch continue_looping to enter while-loop only once
    with patch("sciber_yklocker.YkLock.continue_looping", MagicMock()) as mock_loop:
        mock_loop.side_effect = mock_continue_looping
        # Skip registry updates
        with patch("sciber_yklocker.get_my_platform", MagicMock()):
            # Dont actually lock the device during tests
            with patch("sciber_yklocker.YkLock.lock", MagicMock()) as mock_lock:
                # Patch logger to catch messages
                with patch("sciber_yklocker.YkLock.logger", MagicMock()) as mock_logger:
                    loop_code(MagicMock(), yklocker)

                    # Make sure we got the right message
                    mock_logger.assert_called_with(
                        "YubiKey not found. Locking workstation"
                    )

                # Make sure lock was called, no arguments expected
                mock_lock.assert_called_once_with()


def test_loop_code_with_yubikey():
    yklocker = YkLock()
    # Patch sleep and connection
    yklocker.get_timeout = lambda: 0
    yklocker.is_yubikey_connected = lambda: True

    # Get the global counter and set it to zero
    global temp_counter
    temp_counter = 0

    # Patch continue_looping to enter while-loop only once
    with patch("sciber_yklocker.YkLock.continue_looping", MagicMock()) as mock_loop:
        mock_loop.side_effect = mock_continue_looping
        # Skip registry updates
        with patch("sciber_yklocker.get_my_platform", MagicMock()):
            # Dont actually lock the device during tests
            with patch("sciber_yklocker.YkLock.lock", MagicMock()) as mock_lock:
                # Patch logger to catch messages
                with patch("sciber_yklocker.YkLock.logger", MagicMock()):
                    loop_code(MagicMock(), yklocker)
                # Make sure lock was not called
                mock_lock.assert_not_called()


def test_init_yklocker_win():
    if get_my_platform() == MyPlatform.WIN:
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


def test_init_yklocker_lx():
    if get_my_platform() == MyPlatform.LX or get_my_platform() == MyPlatform.MAC:
        yklocker = init_yklocker(RemovalOption.LOGOUT, 15)
        assert yklocker.get_removal_option() == RemovalOption.LOGOUT
        assert yklocker.get_timeout() == 15


def test_main_no_args():
    # Make sure we go into the argument checks
    with patch(
        "sciber_yklocker.get_my_platform", MagicMock(return_value=MyPlatform.LX)
    ):
        # Dont go inte the loop but make sure it was called
        with patch("sciber_yklocker.loop_code", MagicMock()) as mock_loop_code:
            with patch(
                "sciber_yklocker.init_yklocker", MagicMock()
            ) as mock_init_yklocker:
                main([""])
                mock_init_yklocker.assert_called_once_with(None, None)
                mock_loop_code.assert_called_once()


def test_main_with_logout():
    # Make sure we go into the argument checks
    with patch(
        "sciber_yklocker.get_my_platform", MagicMock(return_value=MyPlatform.LX)
    ):
        # Dont go inte the loop but make sure it was called
        with patch("sciber_yklocker.loop_code", MagicMock()) as mock_loop_code:
            with patch(
                "sciber_yklocker.init_yklocker", MagicMock()
            ) as mock_init_yklocker:
                main(["-l", "Logout", "-t", "5"])
                mock_loop_code.assert_called_once()
                mock_init_yklocker.assert_called_once_with(RemovalOption.LOGOUT, 5)


def test_main_with_doNothing():
    # Make sure we go into the argument checks
    with patch(
        "sciber_yklocker.get_my_platform", MagicMock(return_value=MyPlatform.LX)
    ):
        # Dont go inte the loop but make sure it was called
        with patch("sciber_yklocker.loop_code", MagicMock()) as mock_loop_code:
            with patch(
                "sciber_yklocker.init_yklocker", MagicMock()
            ) as mock_init_yklocker:
                main(["-l", "doNothing", "-t", "5"])
                mock_loop_code.assert_called_once()
                mock_init_yklocker.assert_called_once_with(RemovalOption.NOTHING, 5)


def test_main_with_lock():
    # Make sure we go into the argument checks
    with patch(
        "sciber_yklocker.get_my_platform", MagicMock(return_value=MyPlatform.LX)
    ):
        # Dont go inte the loop but make sure it was called
        with patch("sciber_yklocker.loop_code", MagicMock()) as mock_loop_code:
            with patch(
                "sciber_yklocker.init_yklocker", MagicMock()
            ) as mock_init_yklocker:
                main(["-l", "Lock", "-t", "5"])
                mock_loop_code.assert_called_once()
                mock_init_yklocker.assert_called_once_with(RemovalOption.LOCK, 5)
