from enum import Enum, StrEnum  # StrEnum is python 3.11+


class MyPlatform(Enum):
    MAC = 0
    WIN = 1
    LX = 2
    UNKNOWN = -1


class RemovalOption(StrEnum):
    LOCK = "Lock"
    LOGOUT = "Logout"
    NOTHING = "doNothing"
