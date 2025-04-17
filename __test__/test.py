import re
import unittest


class Test(unittest.TestCase):
    def test(self):

        a = {}
        a[tuple()] = 10
        print(a[tuple()])
        s = re.compile('[^abcd-e]')
        print(s.match('a'))
        print(s.match('b'))
        print(s.match('c'))

    a, (b, c) = (1, (2, 3))