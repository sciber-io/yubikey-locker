from enum import StrEnum  # StrEnum is python 3.11+


class RemovalOption(StrEnum):
    LOCK = "Lock"
    LOGOUT = "Logout"
    NOTHING = "doNothing"
