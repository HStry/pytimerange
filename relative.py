def days(seconds):
    seconds_per_day = 86400
    tolerance_dst = 7200

    _days = round(seconds / seconds_per_day)
    if _days == 0:
        return None

    difference = abs(seconds - (_days * seconds_per_day))

    if difference <= tolerance_dst:
        return _days

    return None


def months(seconds):
    seconds_per_day = 86400
    tolerance_dst = 7200

    def leap(year, month):
        return (month == 0 and year % 4 == 3 and year % 400 not in (3, 103, 203),
                month == 11 and year % 4 == 0 and year % 400 not in (196, 296, 396))

    def m_up(year, month):
        month += 1
        return year + month // 12, month % 12

    def second_limits(day_limits):
        ldn, lup = day_limits
        return ((day * seconds_per_day - tolerance_dst,
                 day * seconds_per_day + tolerance_dst)
                for day in range(ldn, lup + 1))

    sign = 1
    if seconds != abs(seconds):
        seconds = abs(seconds)
        sign = -1

    days_per_month = [[28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31, 31],
                      [31, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31, 28]]

    tally_days = [0, 0]
    y, m = 0, 0
    while True:
        cycle_days = [sum(d) for d in zip([dpm[m] for dpm in days_per_month],
                                          tally_days,
                                          leap(y, m))]

        if seconds < (cycle_days[0]) * seconds_per_day - tolerance_dst:
            break

        tally_days = cycle_days

        y, m = m_up(y, m)

    for limits in second_limits(tally_days):
        if limits[0] <= seconds <= limits[1]:
            return sign * (y * 12 + m)

    return None


def quarters(seconds):
    _months = months(seconds)
    if _months and _months % 3 == 0:
        return int(_months / 3)


def trimesters(seconds):
    _months = months(seconds)
    if _months and _months % 4 == 0:
        return int(_months / 4)


def years(seconds):
    _months = months(seconds)
    if _months and _months % 12 == 0:
        return int(_months / 12)


def decades(seconds):
    _months = months(seconds)
    if _months and _months % 120 == 0:
        return int(_months / 120)


def centuries(seconds):
    _months = months(seconds)
    if _months and _months % 1200 == 0:
        return int(_months / 1200)


def millenniums(seconds):
    _months = months(seconds)
    if _months and _months % 12000 == 0:
        return int(_months / 12000)
