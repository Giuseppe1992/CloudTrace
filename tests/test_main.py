from unittest import TestCase
from CloudMeasurement import ToxTest


class TestToxTest(TestCase):
    def test_f1(self):
        a = ToxTest()
        self.assertEqual(a.f1(), 0)
