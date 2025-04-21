# @encoding: utf-8
# @author: anishan
# @date: 2025/04/17
# @description:
import itertools
from dataclasses import dataclass
from typing import Iterator

ExpressionType = tuple[tuple['ProductionItem', ...], ...]
PARSER_EPSILON = tuple()
PARSER_EMPTY_CHAR = PARSER_EPSILON


@dataclass(frozen=True)
class ParseToken:
    value: str
    end: bool

    @staticmethod
    def terminal(value: str) -> 'ParseToken':
        return ParseToken(value, False)

    def __str__(self):
        return self.value

    def __repr__(self):
        return self.value

PARSER_END = ParseToken("$$$", end=True)

@dataclass(frozen=True)
class ProductionItem:
    """
    For terminated node name is itself.
    For non-terminated node, name is expression name
    """
    is_terminated: bool
    name: str

    def __str__(self) -> str:
        return self.name
    def __repr__(self) -> str:
        return self.name
    def __hash__(self) -> int:
        return hash((self.name, self.is_terminated))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ProductionItem):
            return False
        return self.name == other.name and self.is_terminated == other.is_terminated

@dataclass(frozen=True)
class Production:
    """
    expression is stored by tuple, alternation is stored by outer tuple ((expr,), (expr,))
    """
    name: str                                       # Production name (such as  'A' -> ...)
    expression: ExpressionType                      # Production expression (suck as A -> 'A | B')
    first_set: frozenset[str | tuple]               # First set

    @staticmethod
    def is_epsilon(x):
        return x == PARSER_EPSILON

    def __post_init__(self):
        for expr in self.expression:
            if not isinstance(expr, tuple):
                raise TypeError("Expression must be a tuple")


    def get_first(self) -> set[ProductionItem | tuple]:
        """
        get the first 'production' instead of the first set, just the first product or char
        """
        first = set()
        for expr in self.expression:
            first.add(PARSER_EPSILON if len(expr) == 0 else expr[0])

        return first

    @property
    def alternation_size(self) -> int:
        return len(self.expression)

    def production_size(self, idx) -> int:
        return len(self.expression[idx])

    def get(self, i: int, j: int) -> ProductionItem:
        """
        get ProductionItem
        :param i: alternative index
        :param j: item index in a production
        """
        return self.expression[i][j]

    def split_alternative(self):
        """
        split all alternatives to multi productions
        :return:
        """
        productions = []
        for expr in self.expression:
            productions.append(Production(self.name, (expr, ), self.first_set))

        return productions

    def __eq__(self, other):
        if type(self) is not type(other):
            return False
        return self.name == other.name and self.expression == self.expression

    def __hash__(self):
        return hash((self.name, self.expression))

    def __str__(self):

        expressions = []

        for expr in self.expression:
            expr_string_buff = []

            for c in expr:
                expr_string_buff.append(c.name)

            if expr == tuple():
                expr_string_buff.append('ε')

            expressions.append("".join(expr_string_buff))



        return f"{self.name} -> {' | '.join(expressions)}"

    def __repr__(self):
        first = set(self.first_set)
        if tuple() in first:
            first.remove(tuple())
            first.add('ε')
        return f"{self.__str__()} {first}"

@dataclass(frozen=False)
class WeakProduction:
    """
    for convenient purpose, WeakProduction is the mutable version of Production
    """
    name: str                                                       # Production name (such as  'A' -> ...)
    expression: list[list[ProductionItem]]                          # Production expression (suck as A -> 'A | B')
    first_set: set[str | tuple]          # First set


    def to_production(self) -> Production:
        expressions: list[tuple[ProductionItem, ...]] = []

        for expr in self.expression:
            expressions.append(tuple(expr))

        return Production(self.name, tuple(expressions), frozenset(self.first_set))



@dataclass(frozen=True)
class LR1Item:
    """
    LR1 item, one lookahead char
    LR1 item require single production without alternatives
    """
    production: Production
    position: int                       # dot position
    lookahead: frozenset[ParseToken] | None    # 展望串

    @property
    def size(self):
        """
        production size
        """
        return self.production.production_size(0)

    @property
    def max_pos(self):
        """
        max position, usually equals size + 1, meaning this item needs to be reduced
        """
        return self.size

    def is_end(self):
        """
        :return: if item reaches the end of production
        """
        return self.size == self.position

    def __post_init__(self):
        if self.production.alternation_size > 1:
            raise ValueError("LR1Item can only have one alternation")
        elif not 0 <= self.position <= self.size:
            raise IndexError(f"position out of range, max: {len(self.lookahead)}, current: {self.position}")

    def get_iter(self) -> Iterator[ProductionItem]:
        """
        next production item
        """
        return itertools.islice(self.production.expression[0], self.position, None)

    def get_next(self) -> ProductionItem | None:
        try:
            return next(self.get_iter())
        except StopIteration:
            return None

    def move_next(self) -> 'LR1Item':
        if self.is_end():
            raise IndexError("This LR1Item have already ended")

        return LR1Item(self.production, self.position + 1, self.lookahead)


    def __hash__(self):
        return hash((self.production, self.position, self.lookahead))

    def __eq__(self, other):
        if type(self) is not type(other):
            return False
        return self.production == other.production and \
            self.position == other.position and \
            self.lookahead == other.lookahead

    def __str__(self):
        item_str = []

        i = 0
        for i in range(self.size):
            if i == self.position:
                item_str.append('·')
            item_str.append(self.production.get(0, i).name)


        if i + 1 == self.position:
            item_str.append('·')


        return f"[{self.production.name} -> {' '.join(item_str)}, {set(self.lookahead)}]"

    def __repr__(self):
        return self.__str__()