from enum import StrEnum  # StrEnum is python 3.11+

WIN = "Windows"
MAC = "Darwin"
LX = "Linux"


class MyOS(StrEnum):
    WIN = "Windows"
    MAC = "Darwin"
    LX = "Linux"


class RemovalOption(StrEnum):
    LOCK = "Lock"
    LOGOUT = "Logout"
    NOTHING = "doNothing"
