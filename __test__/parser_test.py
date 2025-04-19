import unittest

from parser.parser_type import Production
from parser.production_builder import ProductionBuilder
from parser.util import compute_first_set


class TestParser(unittest.TestCase):
    def test_parser(self):
        production = ProductionBuilder([
            ("A", ("A+B", "B+A")),
            ("B", ("C*D", "D*C")),
            ("C", ("a", "Dc")),
            ("D", ("123", "(D)")),
        ])
        productions = production.parse()
        print(productions)

        productions = compute_first_set(productions)
        print(productions)
