"""
Tests example
"""

from django.test import SimpleTestCase

from . import clac


class CalcTests(SimpleTestCase):
    # Test clac module

    def test_add_numbers(self):
        res = clac.add(11, 15)
        self.assertEqual(res, 26)

    # TDD: add test before writing actual code
    def test_sub_numbers(self):
        ret = clac.sub(10, 15)
        self.assertEqual(ret, -5)
