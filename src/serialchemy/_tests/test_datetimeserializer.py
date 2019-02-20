from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import Column, DateTime

from serialchemy.datetime_serializer import DateTimeSerializer


@pytest.mark.parametrize("serialized_date", [
    "1994-07-17T20:53",
    "1994-07-17 20:53:00",
    "1994-07-17T20:53:00.000"
])
def test_datetime(serialized_date):
    date_obj = datetime(1994, 7, 17, 20, 53)
    assert date_obj == DateTimeSerializer.load(serialized_date)


def test_datetime_with_sec_tz():
    serializer = DateTimeSerializer
    assert datetime(1994, 7, 17, 20, 53, 12, tzinfo=timezone.utc) == serializer.load("1994-07-17T20:53:12+0000")
    assert datetime(1994, 7, 17, 20, 53, 12, tzinfo=timezone.utc) == serializer.load("1994-07-17T20:53:12Z")
    assert "1994-07-17T20:53:12+00:00" == serializer.dump(serializer.load("1994-07-17T20:53:12Z"))

    assert datetime(1994, 7, 17, 20, 53, 12, 302) == serializer.load("1994-07-17T20:53:12.302")

    assert timezone(timedelta(hours=3)) == serializer.load("1994-07-17T20:53:12+0300").tzinfo
    assert timezone(timedelta(hours=-2, minutes=30)) == serializer.load("1994-07-17T20:53:12.0320-0230").tzinfo

    assert datetime.strptime("1994-07-17T20:53-0030", "%Y-%m-%dT%H:%M%z") == serializer.load("1994-07-17T20:53-0030")
