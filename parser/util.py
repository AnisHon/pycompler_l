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




def __build_dependency(productions: list[Production]):
    """
    build a dependent table, mapping B to {A} if A -> B...
    :param productions:
    :return:
    """
    dependency_table = defaultdict(set)
    for production in productions:
        first_items: Iterable[ProductionItem | tuple] = filter(lambda x: isinstance(x, ProductionItem) and not x.is_terminated, production.get_first())

        for item in first_items:
            dependency_table[item.name].add(production.name)

    return dependency_table


def __update_first_set(name, dependency_table, first_set_table):
    """
    update first set base on dependency_table
    :param name: modified name
    """
    queue: deque = deque()
    queue.append(name)


    while queue:
        name = queue.popleft()
        influenced_names = dependency_table[name]                           # names need to refresh

        visited = set()

        if name in visited:                                                 # in case loop dependency
            continue

        for update_name in influenced_names:

            origin_len = len(first_set_table[update_name])                       # refresh first set
            first_set_table[update_name].update(first_set_table[name])
            current_len = len(first_set_table[update_name])

            if origin_len != current_len:                                   # if modified, continue refresh
                queue.append(update_name)

        if PARSER_EPSILON in first_set_table[name]:
            pass

        visited.add(name)



# def compute_first_set(productions: list[Production]) -> list[Production]:
#     """
#     compute the first set, return new productions (the first set in production.first_set)
#     :return: new productions
#     """
#     __check_duplicate_name(productions)
#
#     result: list[Production] = []
#     productions_table = {production.name: production for production in productions}
#     dependency_table = __build_dependency(productions)
#
#     first_set_table = defaultdict(set)
#
#     for name, production in productions_table.items():
#
#         modified = False
#         for first_element in production.get_first():
#             if first_element.is_terminated:
#                 first_set_table[name].add(first_element.name)
#                 modified = True
#             elif not first_element.is_terminated:
#                 origin_len = len(first_set_table[name])
#                 first_set_table[name].update(first_set_table[first_element.name])
#                 current_len = len(first_set_table[name])
#                 modified = origin_len != current_len
#             else:
#                 first_set_table[name].add(PARSER_EPSILON)
#                 modified = True
#
#
#
#         if modified:
#             __update_first_set(name, dependency_table, first_set_table)
#
#
#     for name  in productions_table:
#         first_set = first_set_table[name]
#         production = productions_table[name]
#         production = Production(production.name, production.expression, frozenset(first_set))
#         result.append(production)
#
#     return result



def __update_first_set(first_sets: dict[str, set], production: Production) -> bool:
    changes = False
    for first in production.get_first():
        if first.is_terminated:
            first_sets[production.name].add(first.name)
            changes = True
        elif PARSER_EPSILON in first_sets[first.name]:



        else:
            before_len = len(first_sets[production.name])
            first_sets[production.name].update(first_sets[first.name])
            after_len = len(first_sets[production.name])

            changes = before_len != after_len




def compute_first(productions: list[Production]) -> list[Production]:
    first_sets: dict[str, set] = defaultdict(set)
    change = True
    while change:
        change = False

        for production in productions:


