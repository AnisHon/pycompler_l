from typing import Iterable, Any

from lex.dfa import DFA
from lex.regex_compiler import RegexLexer, RegexCompiler, DFAOptimizer, N2FConvertor

class Lexer:

    def __initialize(self):
        regex_compiler = RegexCompiler()
        groups, self.__range_map = RegexLexer.parse_group(self.__groups)

        origin, nfa = regex_compiler.compile_group(groups, self.__range_map)

        cvt = N2FConvertor(nfa, origin)
        origin, dfa = cvt.convert()
        # return origin, dfa

        opt = DFAOptimizer(dfa, origin)
        return opt.optimize()

    def __init__(self, pattern_group: Iterable[tuple[Any, str]]):

        self.__groups: Iterable[tuple[str, str]] = pattern_group
        self.__origin, self.__dfa = self.__initialize()

    @property
    def dfa(self) -> DFA:
        return self.__dfa

    @property
    def origin(self) -> int:
        return self.__origin


