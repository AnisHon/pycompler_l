from dataclasses import dataclass

PARSER_EPSILON = tuple()
PARSER_EMPTY_CHAR = PARSER_EPSILON

@dataclass(frozen=True)
class Production:
    """
    推导式
    """
    name: str                                                       # Production name (such as  'A' -> ...)
    expression: tuple[tuple['Production' | str]]                    # Production expression (suck as A -> A | B')
    first_set: frozenset[str]                                       # First set

    @staticmethod
    def is_epsilon(x):
        return x == PARSER_EPSILON

    def get_first_production(self) -> set['Production' | str | tuple ]:
        """
        get the first 'production' instead of first set, just first product
        """
        first = set()
        for expr in self.expression:
            if len(expr) == 0:
                first.add(expr)
            else:
                first.add(expr[0])

        return first




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



