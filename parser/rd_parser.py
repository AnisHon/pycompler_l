"""
Recursive descent Parser
"""
from dataclasses import dataclass

from parser.parser_type import Production, PARSER_EPSILON, ProductionItem, LRItem


@dataclass
class SyntaxNode:
    name: ProductionItem | tuple
    children: list['SyntaxNode']

class RDParser:

    def __init__(self, text, productions: list[Production], init_expr: str):
        self.__text = text
        self.__production_dict = {p.name: p for p in productions}
        self.__idx = 0
        self.__init_expr = self.__production_dict[init_expr]

    def __move_forward(self):
        self.__idx += 1
        if self.__idx > len(self.__text):
            raise RuntimeError("Out of range")

    def __parse_recursive(self, production: Production) -> SyntaxNode:

        idx_cpy = self.__idx
        tree = None
        if production.alternation_size != 1:
            for alter in production.split_alternative():
                tree = self.__parse_recursive(alter)
                if tree:
                    break


        elif production.expression[0] == PARSER_EPSILON:
            node = SyntaxNode(PARSER_EPSILON, [])
            tree = SyntaxNode(ProductionItem(False, production.name), [node])
        else:

            flag = True
            children: list[SyntaxNode] = []
            for item in production.expression[0]:
                temp_node = None
                if item.is_terminated and item.name == self.__text[self.__idx]:
                    self.__move_forward()
                    temp_node = SyntaxNode(item, [])

                elif not item.is_terminated:
                    temp_node = self.__parse_recursive(self.__production_dict[item.name])


                if not temp_node:
                    flag = False
                    break

                children.append(temp_node)

            if flag:
                tree = SyntaxNode(ProductionItem(False, production.name), children)
        if not tree:
            self.__idx = idx_cpy

        return tree




    def parse(self) -> SyntaxNode:
        self.__idx = 0
        return self.__parse_recursive(self.__init_expr)
