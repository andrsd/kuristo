"""
Custom exceptions for kuristo.
"""


class UserException(Exception):
    """
    Exception raised for user-facing errors.

    This exception is caught in __main__ and printed cleanly to the user.
    When --debug flag is enabled, the full traceback is also displayed.
    """

    pass
