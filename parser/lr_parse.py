# @encoding: utf-8
# @author: anishan
# @date: 2025/04/19
# @description: LR1 LALR
import enum
from collections import defaultdict, deque
from dataclasses import dataclass

from common.IdGenerator import id_generator
from parser.parser_type import Production, PARSER_END, LR1Item, PARSER_EPSILON, ProductionItem, ParseToken
from parser.util import compute_first_set

LR1ItemSet = frozenset[LR1Item]

class ParserType(enum.Enum):
    REDUCE = enum.auto()
    SHIFT = enum.auto()
    GOTO = enum.auto()
    ACCEPT = enum.auto()

@dataclass(frozen=True)
class LRTableCell:
    cell_type: ParserType
    value: int

    def __str__(self):
        str_cell_type = ""
        match self.cell_type:
            case ParserType.REDUCE:
                str_cell_type = "r"
            case ParserType.SHIFT:
                str_cell_type = "s"
            case ParserType.ACCEPT:
                str_cell_type = "acc"

        return f"{str_cell_type}{self.value}"

class LR1Parser:
    def __init__(self, productions: list[Production], init_expr: str):
        self.__productions = compute_first_set(productions)
        self.__init_expression = init_expr

        self.__first_set_table: dict[str, frozenset[str | tuple]] = {production.name: production.first_set for production in productions}
        self.production_id_table, self.id_production_table = self.__build_production_id_table()
        self.action_goto_table = self.__parse()

    def __build_production_table(self):
        production_table = {production.name: production.split_alternative() for production in self.__productions}
        if self.__init_expression not in production_table:
            raise RuntimeError(f"The expression {self.__init_expression} is not defined.")

        return production_table

    def __build_production_id_table(self):
        generator = id_generator()
        production_id_table: dict[Production, int] = {}
        for production in self.__productions:
            for expr in production.split_alternative():
                production_id_table[expr] = next(generator)

        id_production_table: dict[int, Production] = {}
        for production, production_id in production_id_table.items():
            id_production_table[production_id] = production

        return production_id_table, id_production_table

    def __compute_lookahead(self, item) -> frozenset[ParseToken]:
        """
        calculate lookahead for the next item,
        for example, A -> a·BC... than this function will calculate lookahead for B
        :param item: it's the item based on computing lookahead
        :return: the lookahead frozenset
        """
        item_iter = item.get_iter()
        lookahead: set[ParseToken] = set()
        try:
            next(item_iter)             # skip the next item, because it's the ower of this lookahead set
        except StopIteration:
            pass


        pos = item.position + 1                     # record position, in case the situation like A -> ...B·
        for production_item in item_iter:
            pos += 1
            if production_item.is_terminated:       # encounter character, done
                lookahead.add(ParseToken.terminal(production_item.name))
                break
            else:                                   # encounter expression, union its first set
                first_set = self.__first_set_table[production_item.name]
                lookahead.update(map(lambda x: ParseToken.terminal(x), filter(lambda x: x != PARSER_EPSILON, first_set)))

                if PARSER_EPSILON not in first_set: # no epsilon found, done
                    break

        if pos == item.max_pos:                 # the calculation reaches the end, union A's lookahead set
            lookahead.update(item.lookahead)

        return frozenset(lookahead)

    def __build_closure_item(self, from_item: LR1Item, to_production: str, production_table):
        productions: set[Production] = production_table[to_production]
        result: set[LR1Item] = set()

        lookahead_set = self.__compute_lookahead(from_item)
        for production in productions:
            result.add(LR1Item(production, position=0,lookahead=lookahead_set))

        return result

    def __item_closure(self, item: LR1Item, production_table):
        """
        just like nfa epsilon closure: A->·B...  =>   B->·...
        :return:
        """
        item_stack = [item]
        result_set:set[LR1Item] = set()

        while item_stack:
            item = item_stack.pop()

            if item in result_set:
                continue

            result_set.add(item)

            if item.is_end():
                continue


            production_item = item.get_next()
            if production_item.is_terminated:
                continue

            closure_set = self.__build_closure_item(item, production_item.name, production_table)
            item_stack.extend(closure_set)

        return result_set

    def __item_go(self, item: LR1Item, production_table) -> tuple[ProductionItem | None, LR1ItemSet]:
        result_set:set[LR1Item] = set()
        if item.is_end():
            return None, frozenset(result_set)

        production_item = item.get_next()

        next_lr1_items = self.__item_closure(item.move_next(), production_table)

        result_set.update(next_lr1_items)


        return production_item, frozenset(result_set)

    def __initialize_deque(self, production_table: dict[str, set[Production]]) -> deque[LR1ItemSet]:
        init_productions = production_table[self.__init_expression]
        items_queue: deque[LR1ItemSet] = deque()
        initial_group = set()
        for item in init_productions:
            initial_group.update(self.__item_closure(LR1Item(item, 0, frozenset([PARSER_END])), production_table))

        items_queue.append(frozenset(initial_group))
        return items_queue

    def __build_production_item(self) -> dict[tuple[LR1ItemSet, ProductionItem], set[LR1Item]]:
        production_table: dict[str, set[Production]] = self.__build_production_table()
        items_queue: deque[LR1ItemSet] = self.__initialize_deque(production_table)

        item_translation_table: dict[tuple[LR1ItemSet, ProductionItem], set[LR1Item]] = defaultdict(set)

        visited = set()

        while items_queue:
            item_set: LR1ItemSet = items_queue.popleft()
            if item_set in visited:
                continue
            visited.add(item_set)

            for item in item_set:
                if item.is_end():
                    continue

                edge, result = self.__item_go(item, production_table)

                item_translation_table[(item_set, edge)].update(result)

            for item in item_set:
                if item.is_end():
                    continue
                production_item = item.get_next()
                items_queue.append(frozenset(item_translation_table[(item_set, production_item)]))


        return item_translation_table

    @staticmethod
    def __build_state_table(item_translation_table: dict[tuple[LR1ItemSet, ProductionItem], set[LR1Item]]) -> dict[LR1ItemSet, int]:
        state_table: dict[LR1ItemSet, int] = {}
        generator = id_generator()
        visited = set()
        for (item_set, item), dest_item_set in item_translation_table.items():
            if item_set not in visited:
                state_table[item_set] = next(generator)
                visited.add(item_set)

            dest_item_set = frozenset(dest_item_set)
            if dest_item_set not in visited:
                state_table[dest_item_set] = next(generator)
                visited.add(dest_item_set)

        return state_table

    def __handle_reduce(self, reduce_set, src_state, action_goto_table):
        if len(reduce_set) == 0:
            return
        for reduce_item in reduce_set:
            production_id = self.production_id_table[reduce_item.production]
            for c in reduce_item.lookahead:
                if reduce_item.production.name == self.__init_expression and c.end:
                    action_goto_table[(src_state, PARSER_END)] = LRTableCell(ParserType.ACCEPT, production_id)
                else:
                    action_goto_table[(src_state, c)] = LRTableCell(ParserType.REDUCE, production_id)

    def __table_type(self, src_item_set: frozenset[LR1Item], dest_item_set: frozenset[LR1Item], item: ProductionItem, state_table) -> dict:
        src_state = state_table[src_item_set]
        dest_state = state_table[dest_item_set]
        action_goto_table = {}



        reduce_set = list(filter(lambda x: x.is_end(), dest_item_set))
        src_reduce_set = list(filter(lambda x: x.is_end(), src_item_set))

        if not item.is_terminated:
            action_goto_table[(src_state, ParseToken.terminal(item.name))] = LRTableCell(ParserType.GOTO, dest_state)
        else:
            action_goto_table[(src_state, ParseToken.terminal(item.name))] = LRTableCell(ParserType.SHIFT, dest_state)

        self.__handle_reduce(src_reduce_set, src_state, action_goto_table)
        self.__handle_reduce(reduce_set, dest_state, action_goto_table)

        return action_goto_table

    def __build_lr1_table(self, item_translation_table: dict[tuple[LR1ItemSet, ProductionItem], set[LR1Item]], state_table: dict[LR1ItemSet, int]):

        action_goto_table: dict[tuple[int, str], LRTableCell] = {}
        for (src_item_set, item), dest_item_set in item_translation_table.items():
            for (src, edge), dest in self.__table_type(src_item_set, frozenset(dest_item_set), item, state_table).items():
                action_goto_table[(src, edge)] = dest
        return action_goto_table

    def __parse(self):
        item_translation_table = self.__build_production_item()

        state_table: dict[LR1ItemSet, int] = LR1Parser.__build_state_table(item_translation_table)

        self.state_table = state_table

        action_goto_table: dict[tuple[int, str], LRTableCell] = self.__build_lr1_table(item_translation_table, state_table)

        for i in action_goto_table:
            print(type(i[1]))

        return action_goto_table


