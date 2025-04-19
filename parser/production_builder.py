import re
from collections import defaultdict

from parser.parser_type import ProductionItem, Production, ExpressionType


class ProductionBuilder:



    def __init_expression_table(self):
        group_by_name = defaultdict(set)
        for name, expression in self.__expressions:
            group_by_name[name].add(expression)

    def __init__(self, expressions: list[tuple[str, tuple[str, ...]]]):
        self.__expression_name = list(map(lambda x: x[0], expressions))
        self.__expressions = expressions


    def __lexer(self) -> list[tuple[str, ExpressionType]]:
        token_specs = [
            ("|".join(self.__expression_name), "E"),
            (".", "T"),
        ]

        token_regex = "|".join(f"(?P<{name}>{pattern})" for pattern, name in token_specs if name)
        token_pattern = re.compile(token_regex, re.VERBOSE)

        productions = []
        for name, expressions in self.__expressions:
            tokens = []

            for expr in expressions:
                tokens.append(tuple([ProductionItem(matched.lastgroup == "T", matched.group()) for matched in token_pattern.finditer(expr)]))


            productions.append((name, tuple(tokens)))


        return productions

    def parse(self):
        expressions = self.__lexer()
        productions = []
        for name, expr_items in expressions:
            productions.append(Production(name, expr_items, frozenset()))

        return productions




