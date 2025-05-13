# @encoding: utf-8
# @author: anishan
# @date: 2025/04/19
# @description: LR1 LALR
import enum
from collections import defaultdict, deque
from dataclasses import dataclass

from common.IdGenerator import id_generator
from parser.parser_type import Production, PARSER_END, LRItem, PARSER_EPSILON, ProductionItem, ParseToken
from parser.util import compute_first_set

LRItemSet = frozenset[LRItem]

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

        self.__first_set_table: dict[str, frozenset[str | tuple]] = {production.name: production.first_set for production in self.__productions}
        self.production_id_table, self.id_production_table = self.__build_production_id_table()

        self.action_goto_table = self.__parse()

    def __build_production_table(self):
        """
        production name -> production alternatives table
        :return:
        """
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

    def _compute_lookahead(self, item) -> frozenset[ParseToken]:
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

            if production_item.is_terminated:       # encounter character, done
                lookahead.add(ParseToken.terminal(production_item.name))
                break
            else:                                   # encounter expression, union its first set
                first_set = self.__first_set_table[production_item.name]
                lookahead.update(map(lambda x: ParseToken.terminal(x), filter(lambda x: x != PARSER_EPSILON, first_set)))

                if PARSER_EPSILON not in first_set: # no epsilon found, done
                    break
            pos += 1

        if pos == item.max_pos:                 # the calculation reaches the end, union A's lookahead set
            lookahead.update(item.lookahead)

        return frozenset(lookahead)

    def _build_closure_item(self, from_item: LRItem, to_production: str, production_table):
        productions: set[Production] = production_table[to_production]
        result: set[LRItem] = set()

        lookahead_set = self._compute_lookahead(from_item)

        for production in productions:
            for lookahead in lookahead_set:
                result.add(LRItem(production, position=0, lookahead=frozenset([lookahead])))

        return result

    def _item_closure(self, item: LRItem, production_table):
        """
        just like nfa epsilon closure: A->·B...  =>   B->·...
        :return:
        """
        item_stack = [item]
        result_set:set[LRItem] = set()

        while item_stack:
            item = item_stack.pop()

            result_set.add(item)

            if item.is_end():
                continue


            production_item = item.get_next()
            if production_item.is_terminated:
                continue

            closure_set = self._build_closure_item(item, production_item.name, production_table)

            for closure_item in closure_set:
                if closure_item not in result_set:
                    item_stack.append(closure_item)

        return result_set

    def __init_production_item(self, production_table):
        """
        build init_expr production Item
        :param production_table:
        :return:
        """
        init_productions = production_table[self.__init_expression]
        return [LRItem(item, 0, frozenset([PARSER_END])) for item in init_productions]

    def __initialize_deque(self, production_table: dict[str, set[Production]]) -> deque[LRItemSet]:
        items_queue: deque[LRItemSet] = deque()

        for item in self.__init_production_item(production_table):
            initial_group = set()
            initial_group.update(self._item_closure(item, production_table))
            items_queue.append(frozenset(initial_group))

        return items_queue


    @staticmethod
    def _group_by_edge(item_collection: LRItemSet) -> dict[ProductionItem, set[LRItem]]:
        edge_items_table: dict[ProductionItem, set[LRItem]] = defaultdict(set)

        for item in item_collection:
            if item.is_end():
                continue
            edge_items_table[item.get_next()].add(item)

        return edge_items_table

    @staticmethod
    def _goto(items, edge, closure_table) -> frozenset[LRItem]:
        """
        similar with DFAEdge + closure function in NFA, this function will move items next level
        :param items: item collection (equals a state in DFA)
        :param edge: transition edge (equals an edge in DFA)
        :return: new items collection
        """
        result_set:set[LRItem] = set()

        for item in items:
            production_item = item.get_next()
            if production_item != edge:
                raise RuntimeError(f"Inconsistent edge expected {edge}, got {production_item}")


            next_lr1_items = closure_table[item.move_next()]
            result_set.update(next_lr1_items)

        return frozenset(result_set)

    def _build_item_collection(self, production_table: dict[str, set[Production]], closure_table) -> set[frozenset[LRItem]]:
        """
        build set of LR1 Canonical Collection
        """
        items_queue: deque[LRItemSet] = self.__initialize_deque(production_table)
        item_groups: set[frozenset[LRItem]] = set()

        while items_queue:
            item_set: LRItemSet = items_queue.popleft()
            item_groups.add(item_set)

            for edge, items in LR1Parser._group_by_edge(item_set).items():
                next_lr1_items = LR1Parser._goto(items, edge, closure_table)
                if next_lr1_items not in item_groups:
                    items_queue.append(next_lr1_items)

        return item_groups

    def __build_closure_table(self, production_table: dict[str, set[Production]]) -> dict[LRItem, set[LRItem]]:
        """
        LRItem -> frozenset[LRItem], cache closure result
        """
        item_queue: deque[LRItem] = deque()
        item_queue.extend(self.__init_production_item(production_table))

        closure_table: dict[LRItem, set[LRItem]] = {}

        while item_queue:
            item = item_queue.popleft()
            closure_items = self._item_closure(item, production_table)
            closure_table[item] = closure_items

            if not item.is_end():
                item = item.move_next()

                if item not in closure_table:
                    item_queue.append(item)

            for item in closure_items:
                if item not in closure_table:
                    item_queue.append(item)

        return closure_table


    @staticmethod
    def __build_state_table(item_collection_set: set[LRItemSet]) -> dict[LRItemSet, int]:
        generator = id_generator()
        return {item_collection: next(generator) for item_collection in item_collection_set}

    @staticmethod
    def __build_state2collection_table(state_table: dict[LRItemSet, int]) -> dict[int, LRItemSet]:
        return {state: item_collection for item_collection, state in state_table.items()}


    def _build_transition_table(self, state_table, closure_table):
        """
        get collection set transition table
        """
        transition_table: dict[tuple[int, ProductionItem], int] = {}
        for item_collection, state in state_table.items():
            for edge, items in self._group_by_edge(item_collection).items():
                dest_item_collection = LR1Parser._goto(items, edge, closure_table)
                dset = state_table[dest_item_collection]
                transition_table[(state, edge)] = dset

        return transition_table


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

    def __table_cell(self, src_state: int, dest_state: int, item: ProductionItem, state_table) -> dict:
        """
        build LR1 table cell
        """
        src_item_set = state_table[src_state]
        dest_item_set = state_table[dest_state]
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

    def __build_lr1_table(self, item_translation_table: dict[tuple[int, ProductionItem], int], state2collection_table: dict[int, LRItemSet]):
        """
        get final lr1 table
        :param item_translation_table: relation table same as dfa transition table
        :param state2collection_table: state -> item collection
        """
        action_goto_table: dict[tuple[int, str], LRTableCell] = {}
        for (src_state, item), dest_state in item_translation_table.items():
            for (src, edge), dest in self.__table_cell(src_state, dest_state, item, state2collection_table).items():
                action_goto_table[(src, edge)] = dest
        return action_goto_table

    def __parse(self):
        production_table = self.__build_production_table()          # name -> production alternatives set

        closure_table = self.__build_closure_table(production_table)    # cache closure (item -> frozenset[item])

        item_collection_set = self._build_item_collection(production_table, closure_table)   # all item collection set

        state_table: dict[LRItemSet, int] = LR1Parser.__build_state_table(item_collection_set)    # item collection -> state

        state2collection_table = LR1Parser.__build_state2collection_table(state_table)          # state -> item collection

        transition_table: dict[tuple[int, ProductionItem], int] = self._build_transition_table(state_table, closure_table)

        self.state_table = state_table                              # for debug
        self.state2collection_table = state2collection_table

        action_goto_table: dict[tuple[int, str], LRTableCell] = self.__build_lr1_table(transition_table, state2collection_table)
        return action_goto_table

class LAlR1Parser(LR1Parser):

    def __init__(self, productions: list[Production], init_expr: str):
        super().__init__(productions, init_expr)

    @staticmethod
    def __merge(item_collection: frozenset[LRItem]):
        lookahead_table = defaultdict(set)
        for item in item_collection:
            lookahead_table[LRItem(item.production, item.position, None)].update(item.lookahead)

        item_collection = set()
        for item, lookahead_ in lookahead_table.items():
            item_collection.add(LRItem(item.production, item.position, frozenset(lookahead_)))


        return frozenset(item_collection)

    @staticmethod
    def __merge_core_equivalent(item_collection_set: set[frozenset[LRItem]]):
        new_item_collection_set: set[frozenset[LRItem]] = set()
        core_table = defaultdict(set)
        for item_collection in item_collection_set:
            core_set = set()
            for item in item_collection:
                core_set.add(LRItem(item.production, item.position, None))

            core_table[frozenset(core_set)].update(item_collection)

        for item_collection in core_table.values():
            new_item_collection_set.add(frozenset(item_collection))

        return new_item_collection_set

    def _build_closure_item(self, from_item: LRItem, to_production: str, production_table):
        productions: set[Production] = production_table[to_production]
        result: set[LRItem] = set()

        lookahead_set = self._compute_lookahead(from_item)
        for production in productions:
            result.add(LRItem(production, position=0, lookahead=lookahead_set))


        return result

    def __refresh_closure_table(self, production_table, item_collection_set, closure_table):
        for item_collection in item_collection_set:
            for item in item_collection:
                closure_items = self._item_closure(item, production_table)
                closure_table[item] = closure_items

    def _build_transition_table(self, state_table, closure_table):
        """
        get collection set transition table
        """
        transition_table: dict[tuple[int, ProductionItem], int] = {}
        for item_collection, state in state_table.items():
            for edge, items in self._group_by_edge(item_collection).items():
                dest_item_collection = LR1Parser._goto(items, edge, closure_table)
                dest_item_collection = LAlR1Parser.__merge(dest_item_collection)
                dset = state_table[dest_item_collection]
                transition_table[(state, edge)] = dset

        return transition_table

    def _build_item_collection(self, production_table: dict[str, set[Production]], closure_table) -> set[frozenset[LRItem]]:
        item_collection_set = super()._build_item_collection(production_table, closure_table)

        item_collection_set = LAlR1Parser.__merge_core_equivalent(item_collection_set)
        item_collection_set = LAlR1Parser.__merge_inner(item_collection_set)

        self.__refresh_closure_table(production_table, item_collection_set, closure_table)

        return item_collection_set

    pass
