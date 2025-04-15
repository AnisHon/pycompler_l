import re
import unittest


class Test(unittest.TestCase):
    def test(self):
        s = re.compile('[^abcd-e]')
        print(s.match('a'))
        print(s.match('b'))
        print(s.match('c'))
        print(s.match('d'))