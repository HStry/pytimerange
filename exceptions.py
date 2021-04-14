"""
Exceptions for python-timerange
"""


class TimerangeWarning(UserWarning):
    """Base warning class"""
    pass


class MixedTimeUnitsWarning(TimerangeWarning):
    """Warning for mixing different relative or relative and exact time units"""
    pass


class AmbiguousDSTWarning(TimerangeWarning):
    """Warning raised when dst state cannot be determined."""
    pass
