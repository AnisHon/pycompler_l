import logging
from typing import Iterable, Any

from lex.dfa import DFA
from lex.regex_compiler import RegexLexer, RegexCompiler, DFAOptimizer, N2DConvertor

class Lexer:



    def __initialize(self):
        regex_compiler = RegexCompiler()
        groups, self.__range_map = RegexLexer.parse_group(self.__groups)

        origin, nfa = regex_compiler.compile_group(groups, self.__range_map)

        cvt = N2DConvertor(nfa, origin, enable_multi_label=self.__minimization)
        origin, dfa = cvt.convert()
        # return origin, dfa


        opt_type = DFAOptimizer.LabelType.MULTI if self.__minimization else DFAOptimizer.LabelType.SINGLE
        opt = DFAOptimizer(dfa, origin, opt_type)

        origin, dfa = opt.optimize()

        if not self.__minimization:
            return origin, dfa



        # handle multi-label priority

        priority_map = {val[0]: idx for idx, val in enumerate(self.__groups)}

        terminal_nodes = filter(lambda x: x.accept, dfa.nodes.values())

        for node_info in terminal_nodes:

            final_label = self.__groups[-1][0]
            for label in node_info.label:
                if priority_map[label] < priority_map[final_label]:
                    final_label = label

            node_info.label = final_label

        return origin, dfa



    def __init__(self, pattern_group: list[tuple[Any, str]], minimization: bool = False):
        """
        :param pattern_group:
        :param minimization: if try to minimize in Optimizer(try to split less at the beginning)
        """

        self.__groups: list[tuple[str, str]] = pattern_group
        self.__minimization = minimization
        self.__origin, self.__dfa = self.__initialize()

    def check(self):
        cnt = 0
        names = {item[0] for item in self.__groups}

        if len(names) != len(self.__groups):
            logging.error("duplicated name found!")
            cnt += 1


        all_reachable_labels = set(map(lambda x: x.label, filter(lambda x: x.accept, self.dfa.nodes.values())))

        diff = names - all_reachable_labels
        if diff:
            logging.warning("The following name are not reachable: {}".format(diff))
            cnt += 1

        if cnt == 0:
            print("No Error")

        else:
            logging.warning("found {} error(s)".format(cnt))




    @property
    def dfa(self) -> DFA:
        return self.__dfa

    @property
    def origin(self) -> int:
        return self.__origin


