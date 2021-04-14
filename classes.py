import relative

import warnings

from datetime import datetime as dtdt
from datetime import timedelta as dttd
import pytz
import time
import math
from numbers import *
from collections import namedtuple
from decimal import Decimal

DEFAULT_TIMEZONE = 'UTC'
DEFAULT_TIMEUNIT = 'day'


class Timestamp:
    """Timestamp"""

    def __init__(self, *timestamp):
        self.__val = None
        self.__sval = None

        if not timestamp:
            self.__value = time.time_ns() * 1000
            return

        if isinstance(timestamp[0], self.__class__):
            self.__value = timestamp[0]._value
            return

        n = len(timestamp)

        if n > 3:
            raise TypeError(f'Timestamp takes up to 3 arguments ({n} given)')

        if n > 1 and not all(isinstance(arg, Integral) for arg in timestamp):
            raise TypeError(
                f'Timestamp requires integrals when using multiple arguments')

        if n == 3:
            _sign, _s, _p = timestamp
            if _sign not in (-1, 1):
                raise ValueError('Incorrect sign provided. -1 or 1 allowed.')
            if _s < 0 or _p < 0:
                raise ValueError(
                    'Parameters \'seconds\' and \'picoseconds\' must be > 0')
            self.__value = _sign * (_s * 10 ** 12 + _p)
            return

        elif n == 2:
            _s, _p = timestamp
            if _p < 0:
                raise ValueError('Parameter \'picoseconds\' must be > 0')
            _sign, _s = (-1, 1)[_s >= 0], abs(_s)
            self.__value = _sign * (_s * 10 ** 12 + _p)
            return

        timestamp = timestamp[0]

        if not isinstance(timestamp, Real):
            timestamp = Decimal(timestamp)

        if timestamp >= 10 ** 11:
            # Assume picoseconds provided
            self.__value = int(timestamp)
        elif isinstance(timestamp, Decimal):
            self.__value = int(timestamp * 10 ** 12)
        else:
            # Float inaccuracies will cause rounding errors beyond μs.
            self.__value = round(timestamp * 10 ** 6) * 10 ** 6

    def __repr__(self):
        return f'{self.__class__.__name__}: {str(self)}'

    def __str__(self):
        if not self.__sval:
            self.__sval = f'{int(self)}'
            if self.value[2]:
                _p = f'{self.value[2]:>012d}'.rstrip('0')
                _p = _p.ljust(math.ceil(len(_p) / 3) * 3, '0')
                self.__sval += f'.{_p}'
        return self.__sval

    def __int__(self):
        return self.value[0] * self.value[1]

    def __float__(self):
        return self.__value / 10 ** 12

    @property
    def _value(self):
        return self.__value

    @property
    def value(self):
        if not self.__val:
            _sign = (-1, 1)[self.__value >= 0]
            _s = abs(self.__value) // 10 ** 12
            _p = abs(self.__value) % 10 ** 12
            self.__val = (_sign, _s, _p)
        return self.__val


class Timezone:
    """Timezone"""

    def __init__(self, timezone=None):
        if not timezone:
            timezone = DEFAULT_TIMEZONE
        elif isinstance(timezone, self.__class__):
            timezone = timezone.name

        self.__pytz = pytz.timezone(timezone)
        self.__name = self.__pytz.zone

    def __repr__(self):
        return f'{self.__class__.__name__}: {str(self)}'

    def __str__(self):
        return self.name

    @property
    def name(self):
        return self.__name

    @property
    def pytz(self):
        return self.__pytz


class Unit:
    def __init__(self, unit=None, quantity=None):
        if unit is None:
            unit = DEFAULT_TIMEUNIT
        if quantity is None:
            quantity = 1

        units = {
            'millennium':
                (('year', 1000, True),
                 None,
                 Delta(months=12000)),
            'century':
                (('year', 100, True),
                 None,
                 Delta(months=1200)),
            'decade':
                (('year', 10, True),
                 None,
                 Delta(months=120)),
            'year':
                (('year', 1, True),
                 None,
                 Delta(months=12)),
            'trimester':
                (('month', 4, True),
                 None,
                 Delta(months=4)),
            'quarter':
                (('month', 3, True),
                 None,
                 Delta(months=3)),
            'month':
                (('month', 1, True),
                 None,
                 Delta(months=1)),
            'week':
                (('week', 1, True),
                 None,
                 Delta(days=7)),
            'workweek':
                (('week', 1, True),
                 None,
                 Delta(days=5)),
            'day':
                (('day', 1, True),
                 None,
                 Delta(days=1)),
            'night':
                (('day', 1, False),
                 None,
                 Delta(days=0.25)),
            'morning':
                (('day', 1, False),
                 Delta(days=0.25),
                 Delta(days=0.25)),
            'afternoon':
                (('day', 1, False),
                 Delta(days=0.5),
                 Delta(days=0.25)),
            'evening':
                (('day', 1, False),
                 Delta(days=0.75),
                 Delta(days=0.25)),
            'hour':
                (('hour', 1, True),
                 None,
                 Delta(seconds=3600)),
            'minute':
                (('minute', 1, True),
                 None,
                 Delta(seconds=60)),
            'second':
                (('second', 1, True),
                 None,
                 Delta(seconds=1)),
            'millisecond':
                (('millisecond', 1, True),
                 None,
                 Delta(picoseconds=10 ** 9)),
            'microsecond':
                (('microsecond', 1, True),
                 None,
                 Delta(picoseconds=10 ** 6)),
            'nanosecond':
                (('nanosecond', 1, True),
                 None,
                 Delta(picoseconds=1000)),
            'picosecond':
                (('picosecond', 1, True),
                 None,
                 Delta(picoseconds=1))
        }

        if unit not in units:
            raise ValueError(f'Unknown time unit \'{unit}\'.')
        if int(quantity) != quantity:
            raise TypeError('Parameter \'quantity\' must be, or be equivalent to, an integer')

        self.__unit = unit
        self.__unit_pars = units[unit]
        self.__quantity = int(quantity)

    @property
    def unit(self):
        return self.__unit

    @property
    def floor_options(self):
        pars = self.__unit_pars[0]
        if pars[2]:
            return {pars[0]: pars[1] * self.__quantity}
        else:
            return {pars[0]: pars[1]}

    @property
    def floor_offset(self):
        return self.__unit_pars[1]

    @property
    def quantity(self):
        return self.__unit_pars[2] * self.__quantity


class Delta:
    """Delta"""

    def __init__(self, *, months=0, days=0, seconds=0, picoseconds=0, **kwargs):
        months += kwargs.get('millenniums', 0) * 12000
        months += kwargs.get('centuries', 0) * 1200
        months += kwargs.get('decades', 0) * 120
        months += kwargs.get('years', 0) * 12
        months += kwargs.get('trimesters', 0) * 4
        months += kwargs.get('quarters', 0) * 3
        days += kwargs.get('weeks', 0) * 7
        seconds += kwargs.get('hours', 0) * 3600
        seconds += kwargs.get('minutes', 0) * 60
        picoseconds += kwargs.get('milliseconds', 0) * 10 ** 9
        picoseconds += kwargs.get('microseconds', 0) * 10 ** 6
        picoseconds += kwargs.get('nanoseconds', 0) * 1000

        if months % 1 != 0:
            raise ValueError('Parameter \'months\' must be an integer, or integer-like.')
        if days * 4 % 1 != 0:
            raise ValueError('Parameter \'days\' must be a multiple of fourths.')
        if picoseconds % 1 != 0:
            raise ValueError('Parameter \'picoseconds\' must be an integer, or integer-like.')

        # Relative time units:
        self.__m = int(months)
        if days % 1 == 0:
            days = int(days)
        self.__d = days

        # Exact time units
        self.__s = int(seconds + picoseconds // 10 ** 12)
        self.__p = int((seconds * 10 ** 12 + picoseconds) % 10 ** 12)

        self.__v = (self.__m * 30.436875 + self.__d) * 86400 + self.__s + self.__p / 10 ** 12

        self.__Val = namedtuple('Val', ['m', 'd', 's', 'p', 'v'])
        self.__Value = namedtuple('Value', ['years', 'months', 'days', 'hours', 'minutes', 'seconds',
                                            'milliseconds', 'microseconds', 'nanoseconds', 'picoseconds'])
        self.__Shorthand = namedtuple('Shorthand', ['Y', 'M', 'D', 'h', 'm', 's', 'ms', 'μs', 'ns', 'ps'])

    @classmethod
    def from_datetime(cls, timedelta: dttd, exact=None):
        secs = timedelta.total_seconds()
        if exact:
            return cls(seconds=secs)

        months = relative.months(secs)
        if months:
            return cls(months=months)

        days = relative.days(secs)
        if days:
            return cls(days=days)

        if exact is not None:
            return cls()

        else:
            return cls(seconds=secs)

    @classmethod
    def __make_comparable(cls, self, other):
        if isinstance(other, dttd):
            other = cls.from_datetime(other)
        elif isinstance(other, (int, float)):
            other = cls(seconds=other)

        if isinstance(other, cls):
            cmpval = (bool(self._val.m) * 32 +
                      bool(self._val.d) * 16 +
                      bool(self._val.s or self._val.p) * 8 +
                      bool(other._val.m) * 4 +
                      bool(other._val.d) * 2 +
                      bool(other._val.s or self._val.p))
            if cmpval not in (0, 1, 2, 4, 8, 9, 16, 18, 32, 36):
                warnings.warn('Comparing exact and relative values, or relative '
                              'values of different unit groups, is unreliable.')
            return other
        return None

    def to_relative(self, inplace=False):
        months = relative.months(self.seconds + self.__d * 86400)
        if months:
            months += self.__m
            if inplace:
                self.__init__(months=months)
                return
            return self.__class__(months=months)

        days = relative.days(self.seconds)
        if days:
            days += self.__d
            if inplace:
                self.__init__(months=self.__m, days=days)
                return
            return self.__class__(months=self.__m, days=days)

        if not inplace:
            return self

    def to_exact(self, inplace=False):
        if inplace:
            self.__init__(seconds=self.__v)
            return
        return self.__class__(seconds=self.__v)

    def __repr__(self):
        v = self._val
        repr_str = f'{self.__class__.__name__}: '

        if v.v == 0:
            return repr_str + '0 s'

        if self.relative:
            repr_str += 'relative '
            if abs(v.m) > 24:
                _Y = int(v.m / 12)
                _M = abs(v.m) % 12
            elif abs(v.m) > 0:
                _Y = 0
                _M = v.m
            else:
                _Y, _M = 0, 0

            if _Y and _M:
                repr_str += f'{_Y}y{_M}m'
            elif _Y:
                repr_str += f'{_Y} year(s)'
            elif _M:
                repr_str += f'{_M} month(s)'

            if abs(v.d) > 0:
                if _Y or _M:
                    repr_str += ', '
                repr_str += f'{v.d} day(s)'

        if self.exact:
            if self.relative:
                repr_str += ', '
            repr_str += 'exact '
            if abs(v.s) > 5400:
                _h = int(v.s / 3600)
                _m = int(abs(v.s) / 60 % 60)
                _s = int(abs(v.s) % 60)
            elif abs(v.s) > 90:
                _h = 0
                _m = int(v.s / 60)
                _s = int(abs(v.s) % 60)
            else:
                _h, _m, _s = 0, 0, v.s

            if _h:
                repr_str += f'{_h}'
                if _s:
                    repr_str += f':{_m:>02d}:{_s:>02d}'
                elif _m:
                    repr_str += f':{_m:>02d}'
                repr_str += ' hrs'
            elif _m:
                repr_str += f'{_m}'
                if _s:
                    repr_str += f':{_s:>02d}'
                repr_str += ' min'
            elif _s:
                repr_str += f'{_s} sec'

            if (_h or _m or _s) and v.p:
                repr_str += f' {"+" if v.p > 0 else "-"} ...'

            elif v.p:
                _sign = 1 if v.p > 0 else -1
                _ms = int(abs(v.p) // 10 ** 9)
                _us = int(abs(v.p) // 10 ** 6 % 1000)
                _ns = int(abs(v.p) // 1000 % 1000)
                _ps = int(abs(v.p) % 1000)

                if _ps:
                    if _ms:
                        repr_str += f'{_ms} {_us:>03d} {_ns:>03d} {_ps:>03d}'
                    elif _us:
                        repr_str += f'{_us} {_ns:>03d} {_ps:>03d}'
                    elif _ns:
                        repr_str += f'{_ns} {_ps:>03d}'
                    else:
                        repr_str += f'{_ps}'
                    repr_str += ' ps'
                elif _ns:
                    if _ms:
                        repr_str += f'{_ms} {_us:>03d} {_ns:>03d}'
                    elif _us:
                        repr_str += f'{_us} {_ns:>03d}'
                    else:
                        repr_str += f'{_ns}'
                    repr_str += ' ns'
                elif _us:
                    if _ms:
                        repr_str += f'{_ms} {_us:>03d}'
                    else:
                        repr_str += f'{_us}'
                    repr_str += ' μs'
                else:
                    repr_str += f'{_ms} ms'
        return repr_str

    def __bool__(self):
        return self.exact or self.relative

    def __abs__(self):
        if self._val.v < 0:
            return -self
        return self

    def __neg__(self):
        _m, _d, _s, _p, _ = (-x for x in self._val)
        return self.__class__(months=_m, days=_d, seconds=_s, picoseconds=_p)

    def __add__(self, other):
        other = self.__make_comparable(self, other)
        if other is None:
            raise NotImplementedError()
        _m, _d, _s, _p, _ = (x + y for x, y in zip(self._val, other._val))
        return self.__class__(months=_m, days=_d, seconds=_s, picoseconds=_p)

    def __sub__(self, other):
        other = self.__make_comparable(self, other)
        if other is None:
            raise NotImplementedError()
        _m, _d, _s, _p, _ = (x - y for x, y in zip(self._val, other._val))
        return self.__class__(months=_m, days=_d, seconds=_s, picoseconds=_p)

    def __mul__(self, other):
        if not isinstance(other, (float, int)):
            raise NotImplementedError()
        _m, _d, _s, _p, _ = (x * other for x in self._val)
        return self.__class__(months=_m, days=_d, seconds=_s, picoseconds=_p)

    def __truediv__(self, other):
        if not isinstance(other, (float, int, self.__class__)):
            raise NotImplementedError()
        if isinstance(other, (float, int)):
            _m, _d, _s, _p, _ = (x / other for x in self._val)
            return self.__class__(months=_m, days=_d, seconds=_s, picoseconds=_p)
        else:
            return self._val.v / other._val.v

    def __floordiv__(self, other):
        if not isinstance(other, (float, int, self.__class__)):
            raise NotImplementedError()
        if isinstance(other, (float, int)):
            _m, _d, _s, _p, _ = (x // other for x in self._val)
            return self.__class__(months=_m, days=_d, seconds=_s, picoseconds=_p)
        else:
            return self._val.v // other._val.v

    def __lt__(self, other):
        other = self.__make_comparable(self, other)
        if other is None:
            raise NotImplementedError()
        return self._val.v < other._val.v

    def __eq__(self, other):
        other = self.__make_comparable(self, other)
        if other is None:
            raise NotImplementedError()
        return self._val.v == other._val.v

    def __gt__(self, other):
        other = self.__make_comparable(self, other)
        if other is None:
            raise NotImplementedError()
        return self._val.v > other._val.v

    def __le__(self, other):
        return self < other or self == other

    def __ge__(self, other):
        return self > other or self == other

    @property
    def _val(self):
        return self.__Val(self.__m, self.__d, self.__s, self.__p, self.__v)

    @property
    def relative(self):
        return bool(self._val.m or self._val.d)

    @property
    def exact(self):
        return bool(self._val.s or self._val.p)

    @property
    def value(self):
        _sign_M = 1 if self.__m == abs(self.__m) else -1
        _sign_s = 1 if self.seconds == abs(self.seconds) else -1

        _m = abs(self.__m)
        _s = abs(self.__s)
        _p = abs(self.__p)

        _Y = _sign_M * int(_m // 12)
        _M = _sign_M * int(_m % 12)
        _D = self.__d
        _h = _sign_s * int(_s // 3600)
        _m = _sign_s * int(_s // 60 % 60)
        _s = _sign_s * int(_s % 60)
        _ms = _sign_s * int(_p // 10 ** 9 % 1000)
        _us = _sign_s * int(_p // 10 ** 6 % 1000)
        _ns = _sign_s * int(_p // 1000 % 1000)
        _ps = _sign_s * int(_p % 1000)
        return self.__Value(_Y, _M, _D, _h, _m, _s, _ms, _us, _ns, _ps)

    @property
    def v(self):
        return self.__Shorthand(*self.value)

    @property
    def seconds(self):
        return self.__s + self.__p / 10 ** 12


class Point:
    def __init__(self, timestamp=None, timezone=None):
        """

        :param timestamp:
        :param timezone:
        """
        self.__datetime = None
        self.__Date = namedtuple('Date', ['year', 'month', 'day'])
        self.__Time = namedtuple('Time', ['hour', 'minute', 'second'])

        if isinstance(timestamp, self.__class__):
            timezone = timezone or timestamp.timezone
            timestamp = timestamp.timestamp
        elif isinstance(timestamp, dtdt):
            if timestamp.tzinfo:
                if not timezone:
                    # noinspection PyBroadException
                    try:              timezone = timestamp.tzinfo.zone
                    except Exception: pass
                timestamp = timestamp.timestamp
            if timezone and timestamp.tzinfo:
                timestamp = timestamp.timestamp
            elif timezone and not timestamp.tzinfo:

            if not timezone:
                # noinspection PyBroadException
                try:
                    timezone = timestamp.tzinfo.zone
                except Exception:
                    pass



            timezone = timezone or timestamp.tzinfo.zone

        self.__timestamp = Timestamp(timestamp)
        self.__timezone = Timezone(timezone)

    @classmethod
    def from_datetime(cls, datetime: dtdt, dttimezone=None, timezone=None, dst=None):

        if not datetime.tzinfo:
            if isinstance(dttimezone, (pytz.tzinfo.StaticTzInfo,
                                       pytz.tzinfo.DstTzInfo,
                                       pytz.UTC.__class__)):
                return cls(dttimezone.localize(datetime).timestamp(), timezone)

            components = datetime.timetuple()[:6] + (0, datetime.microsecond)
            return cls.from_components(components, timezone, dst)
        return cls(datetime.timestamp(), timezone)

    @classmethod
    def from_components(cls, components, timezone=None, dst=None):
        while len(components) < 3:
            components.append(1)
        while len(components) < 10:
            components.append(0)

        if (any((component < 1 for component in components[:3])) or
                any((component < 0 for component in components[3:]))):
            raise ValueError('Component values must be positive.')

        _ts = Timestamp(components[5],
                        components[6] * 10 ** 9 +
                        components[7] * 10 ** 6 +
                        components[8] * 1000 +
                        components[9])
        components[5], timestamp_p = _ts.s, _ts.p

        timezone = Timezone(timezone)

        datetime = timezone.pytz.localize(dtdt(*components[:6]))

        dst_up = dtdt.fromtimestamp(datetime.timestamp() + 4500, timezone.pytz).dst()
        dst_dn = dtdt.fromtimestamp(datetime.timestamp() - 4500, timezone.pytz).dst()

        if dst_up != dst_dn and dst is not None:
            # TODO: DST handling
            warnings.warn('Deterministic dst stuff isn\'t available yet.')

        timestamp = Timestamp(datetime.timestamp(), timestamp_p)

        return cls(timestamp, timezone)

    @staticmethod
    def __roundparcheck(**kwargs):
        args = ('year', 'month', 'day', 'hour', 'minute', 'second',
                'millisecond', 'microsecond', 'nanosecond', 'picosecond',
                'millennium', 'century', 'decade', 'week', 'workweek',
                'night', 'morning', 'afternoon', 'evening')

        pars = [(k, v) for k, v in kwargs.items() if k in args and v]
        if len(pars) != 1:
            raise ValueError('Incorrect arguments provided. Exactly one valid parameter must be non-zero.')

        par, val = pars[0]

        if val <= 0 or int(val) != val:
            raise ValueError('Parameter value must be an integer greater than or equal to 1.')

        if par == 'millennium':
            par, val = 'year', val * 1000
        elif par == 'century':
            par, val = 'year', val * 100
        elif par == 'decade':
            par, val = 'year', val * 10
        elif par == 'trimester':
            par, val = 'month', val * 4
        elif par == 'quarter':
            par, val = 'month', val * 3
        elif par == 'minute':
            par, val = 'second', val * 60
        elif par == 'millisecond':
            par, val = 'picosecond', val * 10 ** 9
        elif par == 'microsecond':
            par, val = 'picosecond', val * 10 ** 6
        elif par == 'nanosecond':
            par, val = 'picosecond', val * 1000

        # TODO: Test for valid factors, e.g. 1, 2, 3, 4, 6 months etc

        return par, val

    def floor(self, *, inplace=False, **kwargs):
        par, val = self.__roundparcheck(**kwargs)

        if par in ('second', 'picosecond'):
            if par == 'second':
                val = val * 10 ** 12
            timestamp = Timestamp(pico=(self.timestamp.s * 10 ** 12 + self.timestamp.p) // val * val)

        elif par == 'hour':
            point = Point(self.timestamp.s // 60 * 60, self.timezone)

            timestamp = self.timestamp.s // 60 * 60 - self.time.minute * 60

        if par == 'picosecond':
            if val >= 10 ** 12:
                pass

        print(par, val)
        if inplace:
            raise NotImplementedError()
        else:
            return None

    def ceil(self, *, inplace=False, **kwargs):
        par, val = self.__roundparcheck(**kwargs)

        print(par, val)
        if inplace:
            raise NotImplementedError()
        else:
            return None

    def round(self, *, inplace=False, **kwargs):
        par, val = self.__roundparcheck(**kwargs)

        print(par, val)
        if inplace:
            raise NotImplementedError()
        else:
            return None

    def __repr__(self):
        return (f'{self.__class__.__name__}: '
                f'{self.date.year}-{self.date.month:>02d}-{self.date.day:>02d} '
                f'{self.time.hour:>02d}:{self.time.minute:>02d}:{self.time.second:>06.3f}, '
                f'{self.timezone.name}{" (DST)" if self.dst else ""}')

    def __add__(self, other):
        # TODO: All the things!
        if isinstance(other, dttd):
            other = Delta.from_datetime(other)
        elif isinstance(other, (int, float)):
            other = Delta(seconds=other)
        if not isinstance(other, Delta):
            raise NotImplementedError()

        timestamp = self.timestamp.timestamp
        # todo fix for sign and picoseconds

        if other.relative:
            components = {**dict(zip(self.date._fields, self.date)),
                          **dict(zip(self.time._fields, self.time))}

            components['year'] += other.value.years
            components['month'] += other.value.months
            components['year'] += (components['month'] - 1) // 12
            components['month'] = (components['month'] - 1) % 12 + 1

            timedelta = dttd(days=components['day'] - 1 + other.value.days)
            components['day'] = 1

            timestamp_f = components['second'] % 1
            components['second'] = int(components['second'])

            timestamp = self.timezone.pytz.localize(
                dtdt(*components) + timedelta).timestamp() + timestamp_f

        if other.exact:
            timestamp = Timestamp(timestamp + other.seconds)

        return self.__class__(timestamp, self.timezone)

    def __sub__(self, other):
        if not isinstance(other, self.__class__):
            return self.__add__(-other)
        delta = Delta(seconds=self.timestamp.timestamp - other.timestamp.timestamp)
        delta.to_relative(inplace=True)
        return delta

    def __lt__(self, other):
        if isinstance(other, self.__class__):
            return self.timestamp < other.timestamp
        if isinstance(other, dtdt):
            return self.timestamp < other.timestamp()
        if isinstance(other, Range):
            return self.timestamp < other.limits.min.timestamp
        return self.timestamp < other

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.timestamp == other.timestamp
        if isinstance(other, dtdt):
            return self.timestamp == other.timestamp()
        return self.timestamp == other

    def __gt__(self, other):
        if isinstance(other, self.__class__):
            return self.timestamp > other.timestamp
        if isinstance(other, dtdt):
            return self.timestamp > other.timestamp()
        if isinstance(other, Range):
            return self.timestamp > other.limits.max.timestamp
        return self.timestamp > other

    def __le__(self, other):
        return self < other or self == other

    def __ge__(self, other):
        return self > other or self == other

    @property
    def timestamp(self):
        return self.__timestamp

    @property
    def timezone(self):
        return self.__timezone

    @property
    def datetime(self):
        if self.__datetime is None:
            ts = self.timestamp.timestamp
            tz = self.timezone.pytz
            self.__datetime = dtdt.fromtimestamp(ts, tz)
        return self.__datetime

    @property
    def dst(self):
        return Delta.from_datetime(self.datetime.dst())

    @property
    def date(self):
        return self.__Date(self.datetime.year, self.datetime.month, self.datetime.day)

    @property
    def time(self):
        return self.__Time(self.datetime.hour, self.datetime.minute, self.datetime.second + self.timestamp.p / 10 ** 12)

    @property
    def weekday(self):
        return self.datetime.isoweekday()

    @property
    def weeknum(self):
        return self.datetime.isocalendar()[1]

    @property
    def name(self):
        months = ('January', 'February', 'March', 'April', 'May', 'June',
                  'July', 'August', 'September', 'October', 'November', 'December')
        days = ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday')

        return months[self.date.month - 1], days[self.weekday]


class Range:
    def __init__(self, start, end, timezone=None):
        _range = (Point(start, timezone), Point(end, timezone))
        if _range[0] >= _range[1]:
            raise ValueError('Parameter \'timestamp_start\' not smaller than \'timestamp_end\'.')

        self.__range = _range
        self.__timezone = Timezone(timezone)
        self.Limits = namedtuple('Limits', ['min', 'max'])

    @classmethod
    def from_components(cls, components, timezone=None, dst=None):
        start = Point.from_components(components, timezone, dst)
        while len(components) < 10:
            components.append(None)

        precision = 0
        for component in components[::-1]:
            if component is not None:
                break
            precision += 1
        end = start + Delta(**{'picoseconds': 1, 'nanoseconds': 1,
                               'microseconds': 1, 'milliseconds': 1,
                               'seconds': 1, 'minutes': 1,
                               'hours': 1, 'days': 1,
                               'months': 1, 'years': 1}[precision])
        return cls(start, end, timezone)

    @classmethod
    def from_unit(cls, timepoint, unit, timezone=None):
        pass

    @property
    def limits(self):
        return self.Limits(*self.__range)
