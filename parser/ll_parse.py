from parser.parser_type import Production, PARSER_EPSILON
from parser.util import compute_alter_first_set, compute_follow_set, nullable


class LL1Parser:


    def __init__(self, productions: list[Production], init_expr: str):
        self.productions = productions
        self.init_expr = init_expr
        self.result_table = self.__init_table()


    def __init_table(self):
        first_set, productions = compute_alter_first_set(self.productions)
        follow_set = compute_follow_set(productions, self.init_expr)
        nullable_dict = nullable(productions)


        result_table: dict[tuple[str, str], Production] = {}
        for production, first in first_set.items():
            for c in first:
                if c == PARSER_EPSILON:
                    continue
                result_table[(production.name, c)] = production

            if nullable_dict[production]:
                for c in follow_set[production.name]:
                    # print(c)
                    result_table[(production.name, c)] = production

        return result_table




