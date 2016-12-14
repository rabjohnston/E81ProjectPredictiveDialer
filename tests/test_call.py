from unittest import TestCase
from callstats import CallStats


class TestCall(TestCase):
    def test_dial(self):
        c = CallStats('2013-12-18 13:39:14.810', 'O', 0, 0, '2013-12-18 13:39:40.033', '0cb53c48fef5cdd7:1508f31:14303d706d8:-7447', 0, 0, 0, 0, 0)

        c.dial(100)

