import re
from datetime import datetime, timezone, timedelta
from sqlalchemy import DateTime

from .serializer import ColumnSerializer


class DateTimeSerializer(ColumnSerializer):
    """
    Serializer for DateTime objects
    """

    DATETIME_REGEX = r"(?P<Y>\d{2,4})-(?P<m>\d{2})-(?P<d>\d{2})" + \
                     r"[T ]" + \
                     r"(?P<H>\d{2}):(?P<M>\d{2})(:(?P<S>\d{2}))?(\.(?P<f>\d+))?" + \
                     r"(?P<tz>([\+-]\d{2}:?\d{2})|[Zz])?"

    DATETIME_RE = re.compile(DATETIME_REGEX)

    def dump(self, value):
        return value.isoformat()

    def load(self, serialized):
        match = self.DATETIME_RE.match(serialized)
        if not match:
            raise ValueError("Could not parse DateTime: '{}'".format(serialized))
        parts = match.groupdict()
        dt = datetime(
            int(parts["Y"]), int(parts["m"]), int(parts["d"]),
            int(parts["H"]), int(parts["M"]), int(parts.get("S") or 0), int(parts.get("f") or 0),
            tzinfo=self._parse_tzinfo(parts["tz"])
        )
        return dt

    def _parse_tzinfo(self, offset_str):
        if not offset_str:
            return None
        elif offset_str.upper() == 'Z':
            return timezone.utc
        else:
            hours = int(offset_str[:3])
            minutes = int(offset_str[-2:])
            # Invert minutes sign if hours == 0
            if offset_str[0] == "-" and hours == 0:
                minutes = -minutes
            return timezone(timedelta(hours=hours, minutes=minutes))


def is_datetime_field(col):
    """
    Check if a column is DateTime (or implements DateTime)

    :param Column col: the column object to be checked

    :rtype: bool
    """
    if hasattr(col.type, "impl"):
        return type(col.type.impl) is DateTime
    else:
        return type(col.type) is DateTime
