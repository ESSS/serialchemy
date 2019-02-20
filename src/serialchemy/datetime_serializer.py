import re
from datetime import datetime, timedelta, timezone

from .serializer import Serializer, ColumnSerializer


class DateTimeSerializer(Serializer):
    """
    Serializer for DateTime objects
    """

    DATETIME_REGEX = r"(?P<Y>\d{2,4})-(?P<m>\d{2})-(?P<d>\d{2})" + \
                     r"[T ]" + \
                     r"(?P<H>\d{2}):(?P<M>\d{2})(:(?P<S>\d{2}))?(\.(?P<f>\d+))?" + \
                     r"(?P<tz>([\+-]\d{2}:?\d{2})|[Zz])?"

    DATETIME_RE = re.compile(DATETIME_REGEX)

    @classmethod
    def dump(cls, value):
        return value.isoformat()

    @classmethod
    def load(cls, serialized, session=None):
        match = cls.DATETIME_RE.match(serialized)
        if not match:
            raise ValueError("Could not parse DateTime: '{}'".format(serialized))
        parts = match.groupdict()
        dt = datetime(
            int(parts["Y"]), int(parts["m"]), int(parts["d"]),
            int(parts["H"]), int(parts["M"]), int(parts.get("S") or 0), int(parts.get("f") or 0),
            tzinfo=cls._parse_tzinfo(parts["tz"])
        )
        return dt

    @staticmethod
    def _parse_tzinfo(offset_str):
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


class DateTimeColumnSerializer(DateTimeSerializer, ColumnSerializer):
    pass
