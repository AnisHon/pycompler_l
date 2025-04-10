import codecs

from common.IdGenerator import id_generator
from common.type import EPSILON, SymbolType, NodeInfo
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

    def __init__(self):
        self.__generator = id_generator()
        self._op_stack: list[TokenType] = []
        self._calc_stack: list[tuple[int, NFA, int]] = []
        RegexCompiler.__master_pattern = '|'.join(f'(?P<{tok.name}>{pat})' for tok, pat in RegexCompiler.__token_specs) # why tok, pat can be exposed to outside?
        RegexCompiler.__master_re = re.compile(RegexCompiler.__master_pattern)
        # self.do


    @staticmethod
    def lex_regex(pattern: str) -> List[Token]:
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

    def __build_escape_nfa(self, val):
        val = codecs.decode(val, 'unicode-escape')
        self.__build_char_nfa(val)

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
        beg1, nfa1, end1 = self._calc_stack.pop()
        beg2, nfa2, end2 = self._calc_stack.pop()
        nfa.concat(nfa1)
        nfa.concat(nfa2)

        beg, end = self.__next_id(), self.__next_id()

        nfa.add_nodes(beg, end)

        nfa.add_edges((beg, beg1, EPSILON), (beg, beg2, EPSILON), (end1, end, EPSILON), (end2, end, EPSILON))

        # nfa.add_edge(beg, beg1)
        # nfa.add_edge(beg, beg2)
        #
        # nfa.add_edge(end1, end)
        # nfa.add_edge(end2, end)

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


    #
    # def __handle_left_lparen(self):
    #     # ...((...)...)这是唯一能出现这种情况的语句后面会把他弹出去
    #     pass


    def __handle_operator(self, curr_op_typ):
        """
        calculate
        :param curr_op_typ: current operator
        """
        # while len(self._op_stack) >0
        if curr_op_typ == TokenType.RPAREN: # we got ) here, time to calculate all symbol between parent
            self.__handle_left_rparen()
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
            elif tok_type == TokenType.ESCAPE:
                self.__build_escape_nfa(tok_val)
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
        return self.__analysis(tokens)




# if __name__ == '__main__':
    # # print("".join(map(lambda x: x[1], RegexCompiler.lex_regex("a|b(a|b|c)*d[a-c]"))))
    # # print(TokenType.priority(TokenType.AND, TokenType.AND))
    # regex_compiler = RegexCompiler()
    # nfa = regex_compiler.compile("(ab|cd)*abc[ab]")
    # print(nfa[1].nodes)
    # nfa[1].print_edge()