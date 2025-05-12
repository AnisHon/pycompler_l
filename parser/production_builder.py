# @encoding: utf-8
# @author: anishan
# @date: 2025/04/17
# @description:

import re
from collections import defaultdict

from parser.parser_type import ProductionItem, Production, ExpressionType


class ProductionBuilder:



    def __init_expression_table(self):
        group_by_name = defaultdict(set)
        for name, expression in self.__expressions:
            group_by_name[name].add(expression)

    def __init__(self, expressions: list[tuple[str, tuple[str, ...], tuple[str, ...]]], token: list[str]):
        """
        expression name,  expression alternatives, attributive grammar
        :param expressions:
        :param token:
        """
        escaped_char = {'+', '?', '(', ')', '{', '}', '.', '|', '[', ']', '*', '+', '\\'}
        new_tokens = []
        for tok in token:
            new_tok = []
            for c in tok:
                if c in escaped_char:
                    new_tok.append("\\")
                new_tok.append(c)
                # print(new_tok)
            new_tok = "".join(new_tok)
            new_tokens.append(new_tok)
        token = new_tokens
        self.__token = set(token)
        # print(self.__token)
        self.__expression_name = list(map(lambda x: x[0], expressions))
        self.__expressions = expressions

        for name in self.__expressions:
            if name in token:
                raise RuntimeError(f"Conflict token name: {name}")


    def __lexer(self) -> list[tuple[str, ExpressionType]]:
        token_specs = [
            ("|".join(sorted(self.__expression_name, key=len, reverse=True)), "E"),
            ("|".join(self.__token), "T"),
        ]

        token_regex = "|".join(f"(?P<{name}>{pattern})" for pattern, name in token_specs if pattern and name)
        token_pattern = re.compile(token_regex, re.VERBOSE)

        productions = []
        for name, expressions, attr_grammar in self.__expressions:
            if not isinstance(attr_grammar, tuple):
                raise RuntimeError(f"Attribute grammar must be a tuple: {attr_grammar}")
            if len(expressions) != len(attr_grammar):
                raise RuntimeError(f"size not match, ({name}, {expressions}, {attr_grammar})")
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




