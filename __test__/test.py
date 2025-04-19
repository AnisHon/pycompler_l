import re
import unittest


class Test(unittest.TestCase):
    def test(self):

        token_specs = [
            ("|".join(['AA', 'BB', 'CC']), "expr"),
            (".", "terminal"),
        ]

        token_regex = "|".join(f"(?P<{name}>{pattern})" for pattern, name in token_specs if name)
        token_pattern = re.compile(token_regex, re.VERBOSE)

        for c in token_pattern.finditer("AAaBBbCCcsdfsdf"):
            print(c.lastgroup, c.group())