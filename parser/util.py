import collections
from collections import defaultdict, deque
from typing import Iterable

from parser.parser_type import Production, PARSER_EPSILON, PARSER_END, ProductionItem


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


def concat_first(production1: Production, production2: Production):
    result = []
    for sub_production in production2.split_alternative():
        new_expression = list(sub_production.expression) + list(production1.expression)
        result.append(new_expression)





def handle_left_recursion(productions: list[Production]):
    for production in productions:
        for sub_production in production.split_alternative():
            first = list(sub_production.get_first())[0]
            # if isinstance(first, ProductionItem) and not first.is_terminated:






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


def __update_follow_set(follow_set, production_dict, production: Production):
    change = False
    for i in range(production.alternation_size):
        last: ProductionItem | None = None
        for j in range(production.production_size(i)):
            item = production.get(i, j)

            if last is not None:
                before = len(follow_set[last.name])
                if item.is_terminated:
                    follow_set[last.name].add(item.name)
                else:
                    first_set = production_dict[item.name].first_set
                    follow_set[last.name].update(first_set)
                    if PARSER_EPSILON in first_set:
                        follow_set[last.name].update(follow_set[item.name])

                    if PARSER_EPSILON in follow_set:
                        follow_set[last.name].remove(PARSER_EPSILON)


                end = len(follow_set[last.name])

                change = change or (end != before)
                last = None


            if not item.is_terminated:
                last = item


        if last is not None:
            follow_set[last.name].update(follow_set[production.name])

    return change





def compute_follow_set(productions: list[Production], initial: str) -> dict[Production, set[str]]:
    """
    A -> aBc
    A -> acB
    A -> aBCc
    """

    change = True
    follow_set = defaultdict(set)
    follow_set[initial].add(PARSER_END)

    production_dict = {production.name: production for production in productions}
    while change:
        change = False

        for production in productions:
            change = change or __update_follow_set(follow_set, production_dict, production)

    return follow_set



