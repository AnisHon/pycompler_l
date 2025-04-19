from dataclasses import dataclass

ExpressionType = tuple[tuple['ProductionItem', ...], ...]
PARSER_EPSILON = tuple()
PARSER_EMPTY_CHAR = PARSER_EPSILON
END_CHAR = "$$$"

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
        return self.name == other.name

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

    def get(self, i: int, j: int):
        """
        get ProductionItem
        :param i: index of alternative
        :param j: index of production
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
        return self.name == other.name

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
    LR1项目集, LR1 item, one lookahead char
    """
    production: Production
    position: int               # dot position
    lookahead: frozenset[str]   # 展望串

    def __post_init__(self):
        if not 0 <= self.position <= len(self.lookahead):
            raise IndexError(f"position out of range, max: {len(self.lookahead)}, current: {self.position}")




