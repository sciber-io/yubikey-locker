import platform

# Yubikey imports
from ykman.device import list_all_devices  # , scan_devices

from sciber_yklocker.models.myos import MyOS
from sciber_yklocker.models.removaloption import RemovalOption

# Import platform specific code
if platform.system() == MyOS.WIN:
    from sciber_yklocker.lib.win import lock_system, log_message

elif platform.system() == MyOS.LX:
    from sciber_yklocker.lib.lx import lock_system, log_message

elif platform.system() == MyOS.MAC:
    from sciber_yklocker.lib.mac import lock_system, log_message


class YkLock:
    def __init__(self) -> None:
        # Set default values
        self.timeout: int = 10
        self.removal_option: RemovalOption = RemovalOption.NOTHING
        self.service_object = None

    def get_timeout(self) -> int:
        return self.timeout

    def set_timeout(self, timeout: int) -> None:
        if isinstance(timeout, int):
            if timeout > 0:
                self.timeout = timeout

    def get_removal_option(self) -> RemovalOption:
        return self.removal_option

    def set_removal_option(self, method: RemovalOption) -> None:
        if method in RemovalOption.__members__.values():
            self.removal_option = method

    def get_service_object(self):
        return self.service_object

    def set_service_object(self, service_object) -> None:
        self.service_object = service_object

    def lock(self) -> None:
        if self.get_removal_option() != RemovalOption.NOTHING:
            lock_system(self.get_removal_option())

    def logger(self, msg: str) -> None:
        log_message(msg)

    def is_yubikey_connected(self) -> bool:
        devices = list_all_devices()
        if len(devices) == 0:
            return False
        else:
            return True
