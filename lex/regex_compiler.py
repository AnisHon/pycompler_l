# @encoding: utf-8
# @author: anishan
# @date: 2025/04/10
# @description: 正则表达式编译，负责 正则解析 正则->NFA 和 NFA->DFA 以及 DFA简化

from itertools import chain
from typing import Any
from collections import deque, defaultdict
from collections.abc import Iterable
from enum import Enum, auto

from common.IdGenerator import id_generator
from common.range_map import RangeMap
from common.common_type import EPSILON, SymbolType, NodeInfo
from common.work_priority_queue import WorkPriorityQueue
from lex.dfa import DFA
from lex.nfa import NFA

MAX_UNICODE_POINT = 0x10FFFF

class TokenType(Enum):

    CHAR = auto()
    DOT = auto()
    STAR = auto()
    PLUS = auto()
    QUESTION = auto()

    OR = auto()
    AND = auto()

    LPAREN = auto()
    RPAREN = auto()
    LBRACKET = auto()
    RBRACKET = auto()

    CHAR_CLASS = auto()
    ESCAPE = auto()
    BACKSLASH = auto()
    DASH = auto()
    HAT = auto()

    _PRIORITY_MAP = {
        LPAREN: {
            LPAREN: -1, RPAREN: 1, AND: 1, OR: 1,
            STAR: 1, PLUS: 1, QUESTION: 1
        },
        AND: {
            LPAREN: -1, RPAREN: 1, AND: 1, OR: 1,
            STAR: -1, PLUS: -1, QUESTION: -1
        },
        OR: {
            LPAREN: -1, RPAREN: 1, AND: -1, OR: 1,
            STAR: -1, PLUS: -1, QUESTION: -1
        },
        STAR: {
            LPAREN: -1, RPAREN: 1, AND: 1, OR: 1,
            STAR: 1, PLUS: 1, QUESTION: 1
        },
        PLUS: {
            LPAREN: -1, RPAREN: 1, AND: 1, OR: 1,
            STAR: 1, PLUS: 1, QUESTION: 1
        },
        QUESTION: {
            LPAREN: -1, RPAREN: 1, AND: 1, OR: 1,
            STAR: 1, PLUS: 1, QUESTION: 1
        }
    }

    def __repr__(self):
        return repr(self.name)

    @classmethod
    def priority(cls, op1, op2):
        try:
            p_map: dict = cls._PRIORITY_MAP.value  # wtf is this? so python, fuck you!
            return p_map[op1.value][op2.value]
        except KeyError:
            raise RuntimeError(f"Impossible Sequence {op1.name} {op2.name}")



class RegexLexer:
    HAT_CHAR = "@^" # spacial mark for ^

    """
    parse regex string into tokens.
    - parse character escapes into char or id
    - parse plain characters into id
    - parse + - * ( ) ? into corresponded token
    - convert characters into char range
    - add explicit add concat
    """

    class LexState(Enum):
        REGULAR = auto()
        CHAR_CLASS = auto()
        ESCAPE = auto()

    def __init__(self):
        pass

    @staticmethod
    def __handle_regular(c: str):
        # characters not in char class
        match c:                        #  converting to dict can be much more elegant
            case '(':
                return TokenType.LPAREN
            case ')':
                return TokenType.RPAREN
            case '[':
                return TokenType.LBRACKET
            case '|':
                return TokenType.OR
            case '*':
                return TokenType.STAR
            case '+':
                return TokenType.PLUS
            case '?':
                return TokenType.QUESTION
            case '.':
                return TokenType.DOT
            case '\\':
                return TokenType.BACKSLASH
            case _:
                return TokenType.CHAR

    @staticmethod
    def __handle_escape(c: str):
        if c in {'d'}:
            return TokenType.ESCAPE
        elif c in {'\\', '[', ']', '{', '}', "(", ")", '-', '.', '+', '?', '|', '*', '"', "'", "/"}:
            return TokenType.CHAR
        else:
            raise RuntimeError(f"Unknown escape character {c}")


    @staticmethod
    def __handle_char_class(c: str):
        match c:                # too short, dict isn't necessary
            case '-':
                return TokenType.DASH
            case '\\':
                return TokenType.BACKSLASH
            case ']':
                return TokenType.RBRACKET
            case '[':
                return TokenType.CHAR               # do not support for nesting char class
            case _:
                return TokenType.CHAR

    @staticmethod
    def __str2token(regex: str):
        """
        convert regex string into tokens, this function will not combine any specific syntax,
        but it does recursively process '[', ']', '\'(escape)
        :param regex: regex pattern
        :return: tokens
        """
        tokens = []
        state_stack = [RegexLexer.LexState.REGULAR] # state stack, escape and '[' need save state

        for i in range(len(regex)):
            c = regex[i]

            state = state_stack[-1]

            match state:
                case RegexLexer.LexState.REGULAR:
                    typ = RegexLexer.__handle_regular(c)
                case RegexLexer.LexState.CHAR_CLASS:
                    typ = RegexLexer.__handle_char_class(c)
                case RegexLexer.LexState.ESCAPE:
                    typ = RegexLexer.__handle_escape(c)
                    state_stack.pop()
                case _:
                    raise RuntimeError(f"Internal Error Unknown State: {c}")

            match typ:
                case TokenType.LBRACKET:
                    state_stack.append(RegexLexer.LexState.CHAR_CLASS)

                case TokenType.RBRACKET:
                    try:
                        state_stack.pop()
                    except IndexError:
                        raise RuntimeError(f"Bucket not match: {i}")

                case TokenType.BACKSLASH:
                    state_stack.append(RegexLexer.LexState.ESCAPE)
                    continue

            tokens.append((typ, c, i))

        if len(state_stack) > 1:
            raise RuntimeError(f"Bucket not close")

        return tokens

    @staticmethod
    def __find_first_rbracket(process_stack) -> int:
        """
        find first '[' in stack
        :param process_stack:
        :return: index of first '['
        """
        i = len(process_stack) - 1
        while process_stack[i][0] != TokenType.LBRACKET:
            i -= 1
        return i

    @staticmethod
    def __build_char_class(process_stack, idx):
        """
        recursively process char class, cast to
        :param process_stack:
        :param idx:
        :return:
        """
        char_class = process_stack[idx + 1:]
        try:
            # '-' at begin or end, just parse as a regular char
            if char_class[0][0] == TokenType.DASH:
                char_class[0] = (TokenType.CHAR, '-', char_class[0][2])
            if char_class[-1][0] == TokenType.DASH:
                char_class[-1] = (TokenType.CHAR, '-', char_class[-1][2])

            # '^' at the beginning, means '^' is operator
            if char_class[0][1] == '^':
                char_class[0] = (TokenType.HAT, '^', char_class[0][2])

            return TokenType.CHAR_CLASS, char_class, char_class[0][2]

        except IndexError:
            raise RuntimeError(f"Empty bucket, idiot. pos: {process_stack[idx][2]}")


    @staticmethod
    def __do_convert(char_ranges):

        temp = []

        dash_flag = False
        for typ, val, pos in char_ranges:

            if typ == TokenType.CHAR:
                if dash_flag:
                    temp.append((temp.pop(), val))
                    dash_flag = False
                else:
                    temp.append(val)
            elif typ == TokenType.CHAR_CLASS:
                if dash_flag:
                    raise RuntimeError(f"Unsupported range at position {pos}")
                temp.extend(RegexLexer.__do_convert(val))
            elif typ == TokenType.DASH:
                dash_flag = True
            elif typ == TokenType.HAT:
                temp.append(RegexLexer.HAT_CHAR)       # spacial mark

        return set(temp)

    @staticmethod
    def __char_class_to_range(tokens):
        """
        process char_class, convert to range(or just single character)
        :param tokens:
        :return:
        """
        i = 0
        while i < len(tokens):
            typ, val, pos = tokens[i]
            if typ == TokenType.CHAR_CLASS:
                char_ranges = RegexLexer.__do_convert(val)
                tokens[i] = (TokenType.CHAR_CLASS, char_ranges, pos)
            i += 1


    @staticmethod
    def __process_char_class(tokens):
        """
        process tokens, convert and combine char class into a recursive structure
        :param tokens:
        :return: tokens
        """
        new_tokens = []
        process_stack = []

        for token in tokens:
            typ = token[0]
            if typ == TokenType.LBRACKET:
                process_stack.append(token)

            elif typ == TokenType.RBRACKET:
                idx = RegexLexer.__find_first_rbracket(process_stack)
                token = RegexLexer.__build_char_class(process_stack, idx)
                del process_stack[idx:]

            if len(process_stack) == 0:
                new_tokens.append(token)

            elif typ != TokenType.LBRACKET:
                process_stack.append(token)

        return new_tokens

    @staticmethod
    def __should_concat(typ1, typ2):
        valid_prev = {
            TokenType.CHAR, TokenType.RPAREN, TokenType.CHAR_CLASS, TokenType.DOT,
            TokenType.ESCAPE, TokenType.STAR, TokenType.PLUS, TokenType.QUESTION  # for postfix: *, +, ?
        }   # c    )   []  \\  * ? +    .
        valid_next = {
            TokenType.CHAR, TokenType.LPAREN, TokenType.CHAR_CLASS,
            TokenType.ESCAPE, TokenType.DOT
        }  # c    (    []    \\
        return typ1 in valid_prev and typ2 in valid_next

    @staticmethod
    def __add_concat(tokens):
        """
        explicit add concat operator
        :return: new tokens with concat operator
        """
        if len(tokens) == 0:
            return tokens
        new_tokens = [tokens[0]]

        i = 1
        while i < len(tokens):
            typ1 = new_tokens[-1][0]
            typ2 = tokens[i][0]

            if RegexLexer.__should_concat(typ1, typ2):
                new_tokens.append((TokenType.AND, '·', tokens[i][2]))
                new_tokens.append(tokens[i])

            else:
                new_tokens.append(tokens[i])

            i += 1

        return new_tokens

    @staticmethod
    def __build_range_map(tokens: Iterable):
        """
        parse token, build range map
        :return: RangeMap
        """

        global MAX_UNICODE_POINT
        range_map = RangeMap()
        range_map.insert(0, MAX_UNICODE_POINT + 1) # cover all Unicode charset

        # I don't if it's standardized, I just don't want to nest too many
        def handle_char_class(char_ranges: set):
            for item in char_ranges:
                if item == RegexLexer.HAT_CHAR:     # spacial operator ^(@^), I don't think it's good idea
                    continue
                elif isinstance(item, str):
                    range_map.insert_single(item)

                else:
                    beg, end = ord(item[0]), ord(item[1]) + 1
                    if beg >= end:
                        raise RuntimeError(f"Bad range {item[0]}-{item[1]} at position {pos}")
                    range_map.insert(beg, end)


        for typ, val, pos in tokens:

            if typ == TokenType.CHAR:
                range_map.insert_single(val)

            elif typ == TokenType.CHAR_CLASS:
                handle_char_class(val)


        generator = id_generator()
        range_map.dfs(ldr_handler=lambda node, *_: node.set_meta(generator.__next__()))

        return range_map

    @staticmethod
    def __calc_whole_set(range_map):

        whole = set()
        range_map.dfs(dlr_handler=lambda x, *_: whole.add(x.meta))

        return whole

    @staticmethod
    def __cvt2range(tokens, range_map):
        """
        convert tokens character with range id(equivalence class)
        :return: new tokens
        """

        whole_set = RegexLexer.__calc_whole_set(range_map)
        new_tokens = []
        def handle_char_class(ranges: set):
            new_range = set()
            for item in ranges:
                if item == RegexLexer.HAT_CHAR:
                    continue

                if isinstance(item, str):
                    new_range.add(range_map.search(item).meta)
                else:
                    beg = range_map.search(item[0]).meta
                    end = range_map.search(item[1]).meta
                    new_range.add(range(beg, end + 1))

            if RegexLexer.HAT_CHAR in ranges:        # 取反
                flattened = {y for x in new_range for y in (x if isinstance(x, Iterable) else {x})}
                new_range = whole_set - flattened

            return new_range

        for typ, val, pos in tokens:
            if typ == TokenType.CHAR:
                new_tokens.append((typ, range_map.search(val).meta, pos))
            elif typ == TokenType.CHAR_CLASS:
               char_ranges = handle_char_class(val)
               new_tokens.append((typ, char_ranges, pos))
            else:
                new_tokens.append((typ, val, pos))
        return new_tokens


    @staticmethod
    def parse(regex: str) -> tuple[list[tuple[TokenType, Any, int]], RangeMap]:

        tokens = RegexLexer.__str2token(regex)
        tokens = RegexLexer.__process_char_class(tokens)
        RegexLexer.__char_class_to_range(tokens)
        range_map = RegexLexer.__build_range_map(tokens)

        tokens = RegexLexer.__cvt2range(tokens, range_map)

        tokens = RegexLexer.__add_concat(tokens)

        return tokens, range_map

    @staticmethod
    def parse_group(regex_groups: Iterable[tuple[Any, str]]) -> tuple[list[tuple[Any, list]], RangeMap]:
        """
        parse group, those group will share same range_map
        :param regex_groups: list of (group_name, regex pattern)
        :return: list of (group_name, tokens), range_map
        """
        token_groups = [(name, RegexLexer.__str2token(pattern)) for name, pattern in regex_groups]
        token_groups = list(map(lambda x: (x[0], RegexLexer.__process_char_class(x[1])), token_groups))
        for _, tokens in token_groups: RegexLexer.__char_class_to_range(tokens)

        chained_tokens = chain(*map(lambda x: x[1], token_groups))
        range_map = RegexLexer.__build_range_map(chained_tokens)

        token_groups = map(lambda x: (x[0], RegexLexer.__cvt2range(x[1], range_map)), token_groups)
        token_groups = list(map(lambda x: (x[0], RegexLexer.__add_concat(x[1])), token_groups))

        return token_groups, range_map


class RegexCompiler:
    """
    compile Tokens into NFA
    """
    Token = tuple[TokenType, str | set | int, int]
    # 正则表达式 -> token 规则

    def __init__(self, generator = None):

        self.__range_map = None
        generator = id_generator() if generator is None else generator

        self.__generator = generator
        self._op_stack: list[TokenType] = []
        self._calc_stack: list[tuple[int, NFA, int]] = []

    def __next_id(self):
        return next(self.__generator)

    def __build_char_nfa(self, edge: SymbolType) -> None:
        nfa = NFA()
        start = self.__next_id()
        end = self.__next_id()
        nfa.add_node(start)
        nfa.add_node(end)

        nfa.add_edge(start, end, edge)

        self._calc_stack.append((start, nfa, end))

    def __build_char_class_nfa(self, tok_val) -> None:

        start = self.__next_id()
        end = self.__next_id()

        nfa = NFA()
        nfa.add_node(start)
        nfa.add_node(end)

        flattened = {y for x in tok_val for y in (x if isinstance(x, Iterable) else {x})}

        for i in flattened:
            state = self.__next_id()
            nfa.add_node(state)
            nfa.add_edge(start, state, i)
            nfa.add_edge(state, end, EPSILON)

        self._calc_stack.append((start, nfa, end))

    def __build_escape_nfa(self, tok_val):
        # todo
        pass

    def __build_dot_nfa(self, _):
        global MAX_UNICODE_POINT

        beg_trans = self.__range_map.search(0).meta
        end_trans = self.__range_map.search(MAX_UNICODE_POINT).meta

        self.__build_char_class_nfa(range(beg_trans, end_trans + 1))


    def __do_calc_concat(self):
        # 注意反向压栈顺序颠倒
        beg1, nfa1, end1 = self._calc_stack.pop()
        beg2, nfa2, end2 = self._calc_stack.pop()
        nfa2.concat(nfa1)
        nfa2.add_edge(end2, beg1, EPSILON)

        self._calc_stack.append((beg2, nfa2, end1))

    def __do_calc_alter(self) -> None:
        nfa = NFA()

        try:
            beg1, nfa1, end1 = self._calc_stack.pop()
            beg2, nfa2, end2 = self._calc_stack.pop()
        except IndexError:
            raise RuntimeError("wrong |")

        nfa.concat(nfa1)
        nfa.concat(nfa2)

        beg, end = self.__next_id(), self.__next_id()

        nfa.add_nodes(beg, end)

        nfa.add_edges((beg, beg1, EPSILON), (beg, beg2, EPSILON), (end1, end, EPSILON), (end2, end, EPSILON))

        self._calc_stack.append((beg, nfa, end))

    def __do_calc_closure(self) -> None:
        beg, nfa, end = self._calc_stack.pop()

        nfa.add_edge(end, beg, EPSILON)
        nfa.add_edge(beg, end, EPSILON)

        self._calc_stack.append((beg, nfa, end))

    def __do_calc_question(self) -> None:
        beg, nfa, end = self._calc_stack.pop()

        nfa.add_edge(beg, end, EPSILON)

        self._calc_stack.append((beg, nfa, end))

    def __do_calc_plus(self) -> None:
        try:
            beg, nfa, end = self._calc_stack.pop()
        except IndexError:
            raise RuntimeError("")


        nfa.add_edge(end, beg, EPSILON)

        self._calc_stack.append((beg, nfa, end))

    def __handle_left_rparen(self):
        # 计算（清空）括号
        op = self._op_stack.pop()
        while op != TokenType.LPAREN:
            self.__CALC_MAP[op]()
            op = self._op_stack.pop()

    def __handle_operator(self, curr_op_typ):
        """
        calculate
        :param curr_op_typ: current operator
        """
        # while len(self._op_stack) >0
        if curr_op_typ == TokenType.RPAREN: # we got ')' here, time to calculate all symbol between parent
            try:
                self.__handle_left_rparen()
            except IndexError:
                raise RuntimeError("括号不匹配")
            return
        elif len(self._op_stack) == 0:       # no operations here, push in
            self._op_stack.append(curr_op_typ)
            return

        top_typ = self._op_stack[-1]        # 栈顶


        if top_typ == TokenType.LPAREN:                         # ( in stack top, we can't do notion about it
            self._op_stack.append(curr_op_typ)

        elif TokenType.priority(top_typ, curr_op_typ) > 0:        # top operator should priorly calculate
            self.__CALC_MAP[top_typ]()
            self._op_stack.pop()

            self.__handle_operator(curr_op_typ)                 # recursively check if it can go on calculating
        else:
            self._op_stack.append(curr_op_typ)                  # current operator should priorly calculate

    def __build_calc_map(self):
        # god jesus, why python syntax dependency resolver so sucks, this function is stupid

        # expand point, if it needs new function, change this table
        self.__CALC_MAP = {
            TokenType.STAR: self.__do_calc_closure,
            TokenType.OR: self.__do_calc_alter,
            TokenType.AND: self.__do_calc_concat,
            TokenType.PLUS: self.__do_calc_plus,
            TokenType.QUESTION: self.__do_calc_question,

        }

    def __analysis(self, tokens: list[Token]) -> tuple[int, NFA, int]:
        self.__build_calc_map()
        for tok in tokens:
            tok_type, tok_val, pos = tok


            # expand point
            match tok_type:
                case TokenType.CHAR: self.__build_char_nfa(tok_val)
                case TokenType.CHAR_CLASS: self.__build_char_class_nfa(tok_val)
                case TokenType.ESCAPE: self.__build_escape_nfa(tok_val)
                case TokenType.DOT: self.__build_dot_nfa(tok_val)
                case _: self.__handle_operator(tok_type)


        # calculate rest of nfa
        while len(self._op_stack) > 0:
            top_typ = self._op_stack.pop()
            self.__CALC_MAP[top_typ]()

        # if still have more than 1 element, it must be wrong
        if len(self._calc_stack) > 1:
            raise SyntaxError("正则解析出错")


        # set terminated state
        nfa_tuple = self._calc_stack.pop()
        nfa_tuple[1].nodes[nfa_tuple[2]].accept = True

        return nfa_tuple

    def compile(self, tokens: list[Token], range_map) -> tuple[int, NFA, int]:
        """
        compile regex to NFA
        :param tokens: regular expr tokens
        :param range_map: range_map generated by Lexer
        :return: (origin state, nfa, terminal state)
        """
        self.__range_map = range_map
        result = self.__analysis(tokens)

        result[1].range_map = range_map
        return result

    def compile_group(self, groups: list[tuple[Any, list[Token]]], range_map):
        self._op_stack: list[TokenType] = []
        self._calc_stack: list[tuple[int, NFA, int]] = []


        nfa_entries = [(name, self.compile(tokens, range_map)) for name, tokens in groups]

        combined_nfa = NFA(range_map)
        origin_state = self.__next_id()
        combined_nfa.add_node(origin_state)

        for idx, entry in enumerate(nfa_entries):
            name, (origin, nfa, dest) = entry
            combined_nfa.concat(nfa)
            combined_nfa.add_edge(origin_state, origin)

            node_info = nfa.nodes[dest]
            node_info.label = name
            node_info.priority = idx

        combined_nfa.range_map = range_map

        return origin_state, combined_nfa


class N2DConvertor:
    """
    Convert NFA to DFA
    """

    def __init_state_table(self):
        """
        this function builds a table associating state with translation symbol(edge)
        """
        for edge in self.nfa.edges:
            state, symbol = edge

            if symbol == EPSILON:     # remove epsilon edge
                continue
            ele = self.__state_table.get(state, set())
            ele.add(symbol)
            self.__state_table[state] = ele


        for node in self.nfa.nodes:
            self.__state_table[node] = self.__state_table.get(node, set())



    def __initialize(self):
        """
        this function initializes calculation queue (with origin_closure)
        """
        self.__init_state_table()

        self.__closure_queue: deque[frozenset[int]] = deque()

        self.__closure_queue.append(self.__origin_closure)  # add initial element





    def __init__(self, nfa: NFA, origin: int, enable_multi_label = False):
        """
        nfa to dfa
        :param nfa: just a nfa
        :param origin: initial state
        :param enable_multi_label: enable multi labels when conflict(multi state cast to single state) occurs
        """
        self.nfa: NFA = nfa
        self.__state_table: dict[int, set[SymbolType]] = {}
        self.__translate_table: dict[tuple[frozenset[int], SymbolType], frozenset[int]] = {} # 转移表，表示k闭包后的转移情况

        self.origin = origin
        self.__origin_closure = frozenset(self.nfa.closure({self.origin}))

        self.__enable_multi_label = enable_multi_label

        self.__initialize()


    @property
    def enable_multi_label(self):
        return self.__enable_multi_label

    def __get_connected(self, states: frozenset[int]):
        """
        this function gets all connected edges(symbol) from set states
        :param states:  set
        """
        connected_edge = set()
        for item in states:
            connected_edge.update(self.__state_table[item])
        return connected_edge




    def __subset_construct(self, state: frozenset[int]):
        """
        construct subset, and add new combination of states into queue
        :param state: multi nfa states correspond to a nfa state
        """
        connected_edge = self.__get_connected(state)
        new_states = set()
        for edge in connected_edge:     # foreach edges(symbols), calculate kleene_closure, fill into transition_table
            connected = frozenset(self.nfa.subset_closure(state, edge))
            self.__translate_table[(state, edge)] = connected
            new_states.add(connected)

        for item in new_states:         # add new state into queue
            self.__closure_queue.append(item)



    @staticmethod
    def __build_id_map(finished_state):
        """
        this function builds a state-id mapping(dict)
        :param finished_state:
        :return: this dict
        """
        state_id_map = {}
        generator = id_generator()


        for state in finished_state:
            state_id_map[state] = next(generator)


        return state_id_map



    @staticmethod
    def __min_priority(node1: NodeInfo, node2: NodeInfo):
        if node1.priority is None and node2.priority is not None:
            return node2

        if node2.priority is None:
            return node1

        if node1.priority > node2.priority:
            return node2
        else:
            return node1

    def __build_node_info(self, states) -> NodeInfo:

        final_node = NodeInfo(False)
        temp_labels = set()


        terminal_state = list(filter(lambda x: self.nfa.nodes[x].accept, states))

        # print(terminal_state)

        for state in terminal_state:  # if it has terminated state, inherit its attribute

            node = self.nfa.nodes[state]
            final_node.accept = True
            if self.enable_multi_label:
                temp_labels.add(node.label)


            else:
                final_node = N2DConvertor.__min_priority(final_node, node)



        if self.enable_multi_label:
            final_node.label = frozenset(temp_labels)

        return final_node

    def __build_dfa(self, state_id_map):
        """
        this function is responsible for building dfa relying on transition_map
        :param state_id_map: state-id map
        :return: dfa
        """
        dfa = DFA()
        for state in state_id_map:          # foreach state_id_map add into dfa
            state_id = state_id_map[state]

            node_info = self.__build_node_info(state)

            dfa.add_node(state_id, accept=node_info.accept, label=node_info.label, meta=node_info.meta)



        for item in self.__translate_table:     # (origin, symbol) -> dest
            origin, edge = item
            dest = self.__translate_table[item]

            origin_id = state_id_map[origin]
            dest_id = state_id_map[dest]

            dfa.add_edge(origin_id, dest_id, edge)

        return dfa




    def convert(self):
        """
        convert nfa into dfa
        :return: (origin state, dfa)
        """

        finished_state = set()  # to prevent duplicate calculations, and convenient for build state-id map
        while len(self.__closure_queue) > 0:
            state = self.__closure_queue.popleft()

            if state in finished_state:  # already calculated, skip
                continue

            self.__subset_construct(state)    # closure
            finished_state.add(state)


        state_id_map = N2DConvertor.__build_id_map(finished_state)  # state-id map
        dfa = self.__build_dfa(state_id_map)
        origin_state = state_id_map[self.__origin_closure]          # origin_state closure(origin_state)

        dfa.range_map = self.nfa.range_map

        return origin_state, dfa


class DFAOptimizer:
    """
    Minimize DFA implemented by Hopcroft DFA Minimization algorithm,
    this class try to modular and make the whole process more clear
    """

    class LabelType(Enum):
        SINGLE = auto()
        MULTI = auto()
        DISABLE = auto()

    def __build_node_edge_table(self):
        """
        build table mapping from state id to symbols
        :return:
        """
        for state, symbol in self.dfa.edges:
            symbols = self.__node_edge_map.get(state, set())
            symbols.add(symbol)
            self.__node_edge_map[state] = symbols

        for state in self.dfa.nodes:
            self.__node_edge_map[state] = self.__node_edge_map.get(state, set())


    def __init__(self, dfa: DFA, origin: int, label_type: LabelType=LabelType.SINGLE, check: bool=True):
        """
        construct DFA optimizer, this
        :param dfa:
        :param origin:
        :param label_type:
        :param check:
        """
        self.__check = check
        if not isinstance(dfa, DFA):
            raise TypeError(f"dfa expected: {DFA}, got:{type(dfa)}")

        self.dfa: DFA = dfa
        self.origin = origin
        self.__node_edge_map = {}
        self.__build_node_edge_table()
        self.__label_type = label_type
        self.__generator = id_generator()

    @property
    def label_type(self):
        return self.__label_type


    def __init_split(self):
        """
        spilt by label or accept type
        :return:
        """

        groups = defaultdict(set)               # all divided group

        terminal_set = defaultdict(set)         # terminal divided group

        for state, node_info in self.dfa.nodes.items():

            if self.label_type == self.LabelType.DISABLE:       # disable label, use accept only
                k = node_info.accept
            else:
                k = node_info.label                             # split by label

            groups[k].add(state)                                # group to groups

            if node_info.accept:
                terminal_set[node_info.label].add(state)        # group split for terminal_set




        return map(lambda x: frozenset(x), groups.values()), map(lambda x: frozenset(x), terminal_set.values())


    def __get_translate_edge(self, state: int | Iterable):
        """
        get all connected symbols
        :param state: states or states,
        """
        if isinstance(state, int):
            return self.__node_edge_map[state]
        else:
            translate_edge = set()
            for s in state: translate_edge.update(self.__node_edge_map[s])
            return translate_edge

    def __goto(self, state, symbol):
        """
        same as GOTO in nfa
        """
        return self.dfa.translate_to(state, symbol)

    def __get_pre(self, min_set_: frozenset[int], symbol) -> frozenset[int]:
        all_states = self.dfa.nodes.keys()
        return frozenset({state for state in all_states if self.__goto(state, symbol) in min_set_})


    @staticmethod
    def min_set(x, y):

        return min(x, y, key=lambda x_: len(x_))

    def __minimize(self):
        """
        hopcroft minimize algorithm
        :return: state sets
        """
        initial_split, terminated_split = self.__init_split()

        block_set: set[frozenset[int]] = {item for item in initial_split if item}   # set of Equivalence Class


        work_queue = WorkPriorityQueue(lambda x: len(x))
        work_queue.push(*terminated_split)


        while (min_set := work_queue.pop()) is not None:                    # almost line to line translate from origin pseudocode

            for symbol in self.dfa.alphabet:
                set_a: frozenset[int] = self.__get_pre(min_set, symbol)
                if not set_a:
                    continue

                for block in list(block_set):

                    intersect: frozenset[int] = block & set_a
                    diff: frozenset[int] = block - set_a

                    if not (intersect and diff):
                        continue

                    block_set.remove(block)
                    block_set.update([intersect, diff])

                    if block in work_queue:
                        work_queue.remove(block)
                        work_queue.push(intersect, diff)
                    else:
                        work_queue.push(DFAOptimizer.min_set(intersect, diff))


        return block_set

    def __build_node_info(self, divided_set):
        """
        build node info (new state), label vary from label type
        :param divided_set: state (original dfa) set
        """

        node_info: NodeInfo = NodeInfo(accept=False)
        temp_labels: set = set()

        for origin_state in divided_set:
            origin_node_info = self.dfa.nodes[origin_state]

            if not origin_node_info.accept:
                continue

            node_info.accept = True

            if self.label_type == self.LabelType.SINGLE:

                node_info.label = origin_node_info.label
                node_info.meta = origin_node_info.meta
                node_info.priority = origin_node_info.priority

                break

            elif self.label_type == self.LabelType.MULTI:
                label = origin_node_info.label
                labels = origin_node_info.label if isinstance(label, Iterable) else {label}

                temp_labels.update(labels)


        if self.label_type == self.LabelType.MULTI and node_info.accept:
            node_info.label = frozenset(temp_labels)


        return node_info

    def __build_node_table(self, divided_sets: set[frozenset[int]]) -> tuple[dict, dict]:
        """
        assign id, node_info for each state sets (new state)
        :return:
        """
        generator = self.__generator

        set_state_table = {}    # state set -> new state id
        node_info_table = {}    # new state -> node info


        for divided_set in divided_sets:        # divided_set -> new state
            state = next(generator)
            set_state_table[divided_set] = state

            node_info = self.__build_node_info(divided_set)
            node_info_table[state] = node_info

        return set_state_table, node_info_table

    @staticmethod
    def __build_state_block_ids_table(divided_sets: set[frozenset[int]], set_state_table):
        """
        build a table mapping from state_id of original dfa to current dfa state
        :param divided_sets:
        :param set_state_table:
        :return:
        """
        state_new_states_table = {}

        for divided_set in divided_sets:
            for old_state in divided_set:
                state_new_states_table[old_state] = set_state_table[divided_set]

        return state_new_states_table

    def __build_connect_table(self, state_block_id_table, block_id_table):
        """
        build new states edge
        :return:
        """
        connect_table = {}

        for block, new_origin in block_id_table.items():

            if self.__check:        # check consistency really cost a lot, can be disabled
                self.__check_block_consistency(block, state_block_id_table) # check consistency

            old_origin = next(iter(block))
            edges = self.__get_translate_edge(old_origin)
            for edge in edges:
                old_dest = self.dfa.translate_to(old_origin, edge)
                new_dest = state_block_id_table[old_dest]
                connect_table[(new_origin, edge)] = new_dest            # add relations to table

        return connect_table


    def __build_dfa(self, connect_table: dict, set_state_table: dict, node_info_table):
        """
        build a new minimized DFA
        :return: minimized DFA
        """
        new_dfa = DFA()
        new_dfa.range_map = self.dfa.range_map

        for state in set_state_table.values():
            node_info = node_info_table[state]
            new_dfa.add_node(state, node_info.accept, node_info.label, node_info.meta)

        for (origin, edge), dest in connect_table.items():
            new_dfa.add_edge(origin, dest, edge)

        return new_dfa

    def __find_new_origin(self, set_state_table: dict):

        for k, v in set_state_table.items():
            if self.origin in k:
                return v

        raise RuntimeError("No new origin found")

    def __check_block_consistency(self, block: frozenset[int], state_block_table: dict) -> None:
        """
        检查一个 block 内部状态在所有符号上的转移是否一致。
        一旦发现不一致（即存在不同的目标 block），立即抛出异常。

        :param block: 当前状态划分（frozenset[int]）
        :param state_block_table: 原状态 -> 所在划分块代表状态（合并后用于重映射）
        :raises RuntimeError: 若 block 内存在任一符号上跳转不一致
        """
        all_symbols = self.dfa.alphabet

        for symbol in all_symbols:
            target_blocks = set()
            target2states = defaultdict(set)

            for state in block:
                dest = self.dfa.translate_to(state, symbol)
                if dest is None:
                    continue
                block_id = state_block_table.get(dest)
                target_blocks.add(block_id)

                target2states[block_id].add(state)


            if len(target_blocks) > 1:
                raise RuntimeError(f"Inconsistent transition in block {block} on symbol '{symbol}': {target_blocks}\n{target2states}")

    def optimize(self) -> tuple[int, DFA]:
        block_set = self.__minimize()                # hopcroft minimization

        block_id_table, node_info_table = self.__build_node_table(block_set)       # convert to new state id
        state_block_ids_table = DFAOptimizer.__build_state_block_ids_table(block_set, block_id_table) # mapping state -> new state
        connect_table = self.__build_connect_table(state_block_ids_table, block_id_table)          # mapping new state edges

        new_origin = self.__find_new_origin(block_id_table)                        # find new origin state

        return new_origin, self.__build_dfa(connect_table, block_id_table, node_info_table)  #build new dfa

