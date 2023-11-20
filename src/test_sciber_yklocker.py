import fake_winreg

from sciber_yklocker import initRegCheck, lockMethod, regcheck, ykLock


def test_yklock_getsetLockMethod():
    yklocker = ykLock()
    input = lockMethod.LOCK
    yklocker.setLockMethod(input)
    yklocker.setLockMethod("hello")

    assert yklocker.getLockMethod() == input


def test_yklock_getsetTimeout():
    yklocker = ykLock()
    input = 10
    yklocker.setTimeout(input)
    yklocker.setTimeout("a")
    yklocker.setTimeout(-1)

    assert yklocker.getTimeout() == input


def test_regcheck():
    input = lockMethod.LOCK
    ret = regcheck(fake_winreg, "removalOption", input)
    assert ret == input

    input = 10
    ret = regcheck(fake_winreg, "timeout", input)
    assert int(ret) == input


def test_initRegCheck():
    yklocker = ykLock()
    input1 = lockMethod.LOCK
    input2 = 10
    yklocker.setLockMethod(input1)
    yklocker.setTimeout(input2)

    lockValue, timeoutValue = initRegCheck(fake_winreg, yklocker)
    assert lockValue == input1
    assert timeoutValue == input2
