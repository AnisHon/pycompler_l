# @encoding: utf-8
# @author: anishan
# @date: 2025/04/10
# @description: 正则表达式编译，负责正则->NFA 和 NFA->DFA 以及 DFA简化
import codecs
from collections import deque

from common.IdGenerator import id_generator
from common.type import EPSILON, SymbolType, NodeInfo
from lex.dfa import DFA
from lex.nfa import NFA
import re
from enum import Enum, auto
from typing import List, Tuple


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
    CHAR_CLASS = auto()
    ESCAPE = auto()

    _PRIORITY_MAP = {
        LPAREN: {
            LPAREN: -1,
            RPAREN: 1,
            AND: 1,
            OR: 1,
            STAR: 1,
        },
        # RPAREN: {
        #     LPAREN: -1,
        #     AND: -1,
        #     OR: -1,
        #     STAR: -1,
        # },
        AND: {
            LPAREN: -1,
            RPAREN: 1,
            AND: 1,
            OR: 1,
            STAR: -1,
        },
        OR: {
            LPAREN: -1,
            RPAREN: 1,
            AND: -1,
            OR: 1,
            STAR: -1,
        },
        STAR: {
            LPAREN: -1,
            RPAREN: 1,
            AND: 1,
            OR: 1,
            STAR: 1,
        }
    }

    @staticmethod
    def priority(op1, op2):
        # if op1 is None:
        #     return -1
        try:
            p_map: dict = TokenType._PRIORITY_MAP.value  # wtf is this? so python, fuck you!
            return p_map[op1.value][op2.value]
        except KeyError:
            raise RuntimeError(f"Impossible Sequence {op1.name} {op2.name}")


class RegexCompiler:
    Token = Tuple[TokenType, str]
    # 正则表达式 -> token 规则
    __token_specs = [
        (TokenType.ESCAPE, r'\\.'),  # 转义字符，如 \*、\(
        (TokenType.CHAR_CLASS, r'\[(\^?)(\\.|[^\]\\])+\]'),  # 字符类，如 [a-z]、[^a]
        (TokenType.DOT, r'\.'),
        (TokenType.STAR, r'\*'),
        (TokenType.PLUS, r'\+'),
        (TokenType.QUESTION, r'\?'),
        (TokenType.OR, r'\|'),
        (TokenType.LPAREN, r'\('),
        (TokenType.RPAREN, r'\)'),
        (TokenType.CHAR, r'[^\\\[\]\.\*\+\?\|\(\)]'),  # 非特殊字符
    ]

    __master_pattern = None
    __master_re = None

    def __init__(self, generator = None):

        generator = id_generator() if generator is None else generator

        self.__generator = generator
        self._op_stack: list[TokenType] = []
        self._calc_stack: list[tuple[int, NFA, int]] = []
        RegexCompiler.__master_pattern = '|'.join(f'(?P<{tok.name}>{pat})' for tok, pat in RegexCompiler.__token_specs) # why tok, pat can be exposed to outside?
        RegexCompiler.__master_re = re.compile(RegexCompiler.__master_pattern)
        # self.do

    @staticmethod
    def handle_escape(tokens):
        i = 0
        esc_char = set("()[]{}*|")
        while i < len(tokens):
            item = tokens[i]
            if item[0] != TokenType.ESCAPE:
                i += 1
                continue

            val = item[1][1:]
            if val not in esc_char:
                val = codecs.decode(val, 'unicode-escape')

            tokens[i] = (TokenType.CHAR, val)
            i += 1








    @staticmethod
    def lex_regex(pattern: str) -> List[Token]:
        # todo 以后把他变成自己写的dfa
        tokens = []
        pos = 0
        while pos < len(pattern):
            m = RegexCompiler.__master_re.match(pattern, pos)
            if not m:
                raise SyntaxError(f"无法解析: {pattern[pos:]}")
            typ: str = m.lastgroup
            val: str = m.group()
            tokens.append((TokenType[typ], val))
            pos = m.end()

        RegexCompiler.handle_escape(tokens)

        result = []
        is_char = False

        for item in tokens:
            typ, val = item

            if is_char and (typ == TokenType.CHAR or typ == TokenType.LPAREN or typ == TokenType.CHAR_CLASS):
                result.append((TokenType.AND, 'X'))
                is_char = False

            if typ == TokenType.CHAR or typ == TokenType.RPAREN or typ == TokenType.CHAR_CLASS or typ == TokenType.STAR:
                is_char = True
            else:
                is_char = False
            result.append(item)

        return result

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


        # build iterable object
        if len(tok_val) == 5 and tok_val[2] == '-':
            char_range = range(ord(tok_val[1]), ord(tok_val[3]) + 1)
        else:
            char_range = tok_val[1:-1]      # simple but slow


        for i in char_range:
            c = chr(i) if isinstance(i, int) else i
            state = self.__next_id()
            nfa.add_node(state)
            nfa.add_edge(start, state, c)
            nfa.add_edge(state, end, EPSILON)

        self._calc_stack.append((start, nfa, end))


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
        if curr_op_typ == TokenType.RPAREN: # we got ) here, time to calculate all symbol between parent
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
            return

        if TokenType.priority(top_typ, curr_op_typ) > 0:        # top operator should priorly calculate
            self.__CALC_MAP[top_typ]()
            self._op_stack.pop()

            self.__handle_operator(curr_op_typ)                 # recursively check if can go on calculating
        else:
            self._op_stack.append(curr_op_typ)                  # current operator should priorly calculate

    def __build_calc_map(self):
        # god jesus, why python syntax dependency resolver so sucks, this function is stupid
        self.__CALC_MAP = {
            TokenType.STAR: self.__do_calc_closure,
            TokenType.OR: self.__do_calc_alter,
            TokenType.AND: self.__do_calc_concat,
            # TokenType.LPAREN: self.__handle_left_lparen,
            # TokenType.RPAREN: self.__handle_left_rparen,
        }

    def __analysis(self, tokens: list[Token]) -> tuple[int, NFA, int]:
        self.__build_calc_map()
        for tok in tokens:
            tok_type, tok_val = tok


            if tok_type == TokenType.CHAR:
                self.__build_char_nfa(tok_val)
            elif tok_type == TokenType.CHAR_CLASS:
                self.__build_char_class_nfa(tok_val)
            else:
                self.__handle_operator(tok_type)

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

    def compile(self, regex: str) -> tuple[int, NFA, int]:
        """
        compile regex to NFA
        :param regex: regex expression string
        :return: (origin state, nfa, terminal state)
        """
        tokens = RegexCompiler.lex_regex(regex)
        # print(tokens)
        return self.__analysis(tokens)




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

        return origin_state, dfa








# if __name__ == '__main__':
    # # print("".join(map(lambda x: x[1], RegexCompiler.lex_regex("a|b(a|b|c)*d[a-c]"))))
    # # print(TokenType.priority(TokenType.AND, TokenType.AND))


    # print(nfa[1].nodes)
    # nfa[1].print_edge()
