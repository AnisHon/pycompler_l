import collections
from collections import defaultdict, deque
from typing import Iterable

from parser.parser_type import Production, PARSER_EPSILON, ProductionItem


def __check_duplicate_name(productions: list[Production]):
    counter = defaultdict(int)
    for production in productions:
        counter[production.name] += 1
        if counter[production.name] > 1:
            raise RuntimeError(f"Duplicate productions found for {production.name}")


def __update_first_set(first_sets: dict[str, set], production: Production):
    for i in range(production.alternation_size):
        for j in range(production.production_size(i)):
            item = production.get(i, j)

            if item.is_terminated:                          # terminal character adds to set
                first_sets[production.name].add(item.name)
                break
            else:
                first_sets[production.name].update(first_sets[item.name])   # non-terminal expression concat to set
                if PARSER_EPSILON not in first_sets[item.name]:             # no epsilon inside, break out
                    break






def compute_first_set(productions: list[Production]) -> list[Production]:
    """
    plain way to compute the first set
    :param productions:
    :return:
    """

    __check_duplicate_name(productions)
    first_sets: dict[str, set] = defaultdict(set)
    change = True
    while change:
        change = False

        for production in productions:
            before_len = len(first_sets[production.name])

            __update_first_set(first_sets, production)

            after_len = len(first_sets[production.name])
            change = change or (before_len != after_len)



    return [Production(production.name, production.expression, frozenset(first_sets[production.name])) for production in productions]
