from lib import MyPlatform, RemovalOption
from sciber_yklocker import YkLock, get_my_platform, platform

## Test Functions ##


def test_get_my_platform():
    platform.system = lambda: "nada"
    assert get_my_platform() == MyPlatform.UNKNOWN


def test_yklock_getset_removal_option():
    yklocker = YkLock()
    yklocker.set_removal_option(RemovalOption.LOGOUT)
    yklocker.set_removal_option("hello")
    assert yklocker.get_removal_option() == RemovalOption.LOGOUT

    yklocker.set_removal_option(RemovalOption.LOCK)
    assert yklocker.get_removal_option() == RemovalOption.LOCK

    yklocker.set_removal_option(RemovalOption.NOTHING)
    assert yklocker.get_removal_option() == RemovalOption.NOTHING


def test_yklock_getset_timeout():
    yklocker = YkLock()
    input = 15
    yklocker.set_timeout(input)
    yklocker.set_timeout("a")
    yklocker.set_timeout(-1)

    assert yklocker.get_timeout() == input
