# @encoding: utf-8
# @author: anishan
# @date: 2025/04/10
# @description: 正则表达式编译，负责 正则解析 正则->NFA 和 NFA->DFA 以及 DFA简化

from collections import deque
from collections.abc import Iterable
from enum import Enum, auto

from common.IdGenerator import id_generator
from common.range_map import RangeMap
from common.type import EPSILON, SymbolType
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
            LPAREN: -1,
            RPAREN: 1,
            AND: 1,
            OR: 1,
            STAR: 1,
            PLUS: 1,
            QUESTION: 1
        },
        AND: {
            LPAREN: -1,
            RPAREN: 1,
            AND: 1,
            OR: 1,
            STAR: -1,
            PLUS: -1,
            QUESTION: -1
        },
        OR: {
            LPAREN: -1,
            RPAREN: 1,
            AND: -1,
            OR: 1,
            STAR: -1,
            PLUS: -1,
            QUESTION: -1
        },
        STAR: {
            LPAREN: -1,
            RPAREN: 1,
            AND: 1,
            OR: 1,
            STAR: 1,
            PLUS: 1,
            QUESTION: 1
        },
        PLUS: {
            LPAREN: -1,
            RPAREN: 1,
            AND: 1,
            OR: 1,
            STAR: 1,
            PLUS: 1,
            QUESTION: 1
        },
        QUESTION: {
            LPAREN: -1,
            RPAREN: 1,
            AND: 1,
            OR: 1,
            STAR: 1,
            PLUS: 1,
            QUESTION: 1
        }
    }

    def __repr__(self):
        return repr(self.name)

    @staticmethod
    def priority(op1, op2):
        # if op1 is None:
        #     return -1
        try:
            p_map: dict = TokenType._PRIORITY_MAP.value  # wtf is this? so python, fuck you!
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
        match c:
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
        elif c in {'\\', '[', ']', '{', '}', "(", ")", '-', '.', '+', '?', '|'}:
            return TokenType.CHAR
        else:
            raise RuntimeError(f"Unknown escape character {c}")


    @staticmethod
    def __handle_char_class(c: str):
        match c:
            case '-':
                return TokenType.DASH
            case '\\':
                return TokenType.BACKSLASH
            case ']':
                return TokenType.RBRACKET
            case '[':
                return TokenType.LBRACKET
            case _:
                return TokenType.CHAR

    @staticmethod
    def __str2token(regex: str):
        tokens = []
        state_stack = [RegexLexer.LexState.REGULAR]

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
        i = len(process_stack) - 1
        while process_stack[i][0] != TokenType.LBRACKET:
            i -= 1
        return i

    @staticmethod
    def __build_char_class(process_stack, idx):
        char_class = process_stack[idx + 1:]
        try:
            # '-' at begin or end, juts parse as a char
            if char_class[0][0] == TokenType.DASH:
                char_class[0] = (TokenType.CHAR, '-', char_class[0][2])
            if char_class[-1][0] == TokenType.DASH:
                char_class[-1] = (TokenType.CHAR, '-', char_class[-1][2])

            # '^' at the beginning
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
        i = 0
        while i < len(tokens):
            typ, val, pos = tokens[i]
            if typ == TokenType.CHAR_CLASS:
                char_ranges = RegexLexer.__do_convert(val)
                tokens[i] = (TokenType.CHAR_CLASS, char_ranges, pos)
            i += 1


    @staticmethod
    def __process_char_class(tokens):
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
    def __build_range_map(tokens):
        global MAX_UNICODE_POINT
        range_map = RangeMap()
        range_map.insert(0, MAX_UNICODE_POINT + 1) # cover all Unicode charset

        # I don't if it's standardized, I just don't want to nest too many
        def handle_char_class(char_ranges: set):
            for item in char_ranges:
                if item == RegexLexer.HAT_CHAR:
                    continue
                elif isinstance(item, str):
                    range_map.insert_single(item)

                else:
                    range_map.insert(ord(item[0]), ord(item[1]) + 1)


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
    def __cvt_char_range(tokens, range_map):
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
    def parse(regex: str) -> tuple[list[tuple[TokenType, any, int]], RangeMap]:

        tokens = RegexLexer.__str2token(regex)
        tokens = RegexLexer.__process_char_class(tokens)
        RegexLexer.__char_class_to_range(tokens)
        range_map = RegexLexer.__build_range_map(tokens)

        tokens = RegexLexer.__cvt_char_range(tokens, range_map)

        tokens = RegexLexer.__add_concat(tokens)

        return tokens, range_map




class RegexCompiler:
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
            raise RuntimeError("")

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
        beg, nfa, end = self._calc_stack.pop()

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

        # expand point, if need new function change this table
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




class N2FConvertor:
    """
    NFA to DFA Convertor
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


        # print(self.__state_table)


    def __initialize(self):
        """
        this function initializes calculation queue (with origin_closure)
        """
        self.__init_state_table()

        self.__closure_queue: deque[frozenset[int]] = deque()

        self.__closure_queue.append(self.__origin_closure)  # add initial element





    def __init__(self, nfa: NFA, origin: int):
        self.nfa: NFA = nfa
        self.__state_table: dict[int, set[SymbolType]] = {}
        self.__translate_table: dict[tuple[frozenset[int], SymbolType], frozenset[int]] = {} # 转移表，表示k闭包后的转移情况

        self.origin = origin
        self.__origin_closure = frozenset(self.nfa.closure({self.origin}))

        self.__initialize()




    def __get_connected(self, states: frozenset[int]):
        """
        this function gets all connected edges(symbol) from set states
        :param states:  set
        """
        connected_edge = set()
        for item in states:
            connected_edge.update(self.__state_table[item])
        return connected_edge




    def __kleene_calc(self, state: frozenset[int]):
        """
        calculate kleene closure, meanwhile add new combination of states into queue
        :param state: multi nfa states correspond to a nfa state
        """
        connected_edge = self.__get_connected(state)
        new_states = set()
        for edge in connected_edge:     # foreach edges(symbols), calculate kleene_closure, fill into transition_table
            connected = frozenset(self.nfa.kleene_closure(state, edge))
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

        # print(state_id_map)
        return state_id_map


    def __build_dfa(self, state_id_map):
        """
        this function is responsible for building dfa relying on transition_map
        :param state_id_map: state-id map
        :return: dfa
        """
        dfa = DFA()
        for state in state_id_map:          # foreach state_id_map add into dfa
            state_id = state_id_map[state]
            accept = False
            meta = None
            for node in state:              # if it has terminated state, inherit its attribute
                if self.nfa.nodes[node].accept:
                    accept = True
                    meta = self.nfa.nodes[node].meta
                    break

            dfa.add_node(state_id, accept=accept, meta=meta)

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

            self.__kleene_calc(state)    # closure
            finished_state.add(state)


        state_id_map = N2FConvertor.__build_id_map(finished_state)  # state-id map
        dfa = self.__build_dfa(state_id_map)
        origin_state = state_id_map[self.__origin_closure] # origin_state closure(origin_state)

        dfa.range_map = self.nfa.range_map

        return origin_state, dfa


class DFAOptimizer:
    """
    todo DFA化简 使用Hopcroft算法
    """

    def __build_node_edge_map(self):
        for state, symbol in self.dfa.edges:
            symbols = self.__node_edge_map.get(state, set())
            symbols.add(symbol)
            self.__node_edge_map[state] = symbols

        for state in self.dfa.nodes:
            self.__node_edge_map[state] = self.__node_edge_map.get(state, set())


    def __init__(self, dfa: DFA, origin: int):
        self.dfa: DFA = dfa
        self.origin = origin
        self.__node_edge_map = {}
        self.__build_node_edge_map()


    def __init__split(self):
        non_terminal = set()
        terminal = set()
        for state in self.dfa.nodes:
            if self.dfa.nodes[state].accept:
                terminal.add(state)
            else:
                non_terminal.add(state)

        return [non_terminal, terminal]

    def __get_translate_edge(self, state: int | Iterable):
        if isinstance(state, int):
            return self.__node_edge_map[state]
        else:
            translate_edge = set()
            for s in state: translate_edge.update(s)
            return translate_edge

    def __goto(self, state, symbol):
        return self.dfa.translate_to(state, symbol)

    def __all_in_predicate(self, state, dest_set):
        all_edges = self.__get_translate_edge(state)
        return all(self.__goto(state, edge) in dest_set for edge in all_edges)

    def minimize(self):
        work_stack = self.__init__split()

        while work_stack:
            split_set = work_stack.pop()










# if __name__ == '__main__':
    # # print("".join(map(lambda x: x[1], RegexCompiler.lex_regex("a|b(a|b|c)*d[a-c]"))))
    # # print(TokenType.priority(TokenType.AND, TokenType.AND))


    # print(nfa[1].nodes)
    # nfa[1].print_edge()
