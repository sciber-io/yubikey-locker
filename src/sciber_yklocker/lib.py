from enum import StrEnum  # StrEnum is python 3.11+


class MyOS(StrEnum):
    WIN = "Windows"
    MAC = "Darwin"
    LX = "Linux"


class RemovalOption(StrEnum):
    LOCK = "Lock"
    LOGOUT = "Logout"
    NOTHING = "doNothing"
