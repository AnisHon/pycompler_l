# @encoding: utf-8
# @author: anishan
# @date: 2025/04/10
# @description: 测试用，有NFA转移表打印测试，NFA图测试
import unittest

from graphviz import Digraph
from common.replace_util import ReplaceUtil
from common.type import EPSILON
from lex.regex_compiler import RegexCompiler, N2FConvertor

reg = "cnm|nmsl"


class TestRegexCompiler(unittest.TestCase):
    # def test_compile(self):
    #     # print("".join(map(lambda x: x[1], RegexCompiler.lex_regex("a|b(a|b|c)*d[a-c]"))))
    #     # print(TokenType.priority(TokenType.AND, TokenType.AND))
    #     regex_compiler = RegexCompiler()
    #     nfa = regex_compiler.compile("(ab|cd)*abc[a-b] [123kasdfasdf]")
    #     # print(nfa[1].nodes)
    #     nfa[1].print_edge()



    def test_draw_nfa_picture(self):

        regex_compiler = RegexCompiler()
        com_nfa = regex_compiler.compile(reg)
        nfa = com_nfa[1]
        nfa_p = Digraph(filename="nfa", format='png')

        nfa_p.render()
        for item in nfa.nodes:
            node = nfa.nodes[item]
            # print()
            if item == com_nfa[0]:
                nfa_p.node(str(item), shape='circle', fillcolor="red", style='filled')
            elif node.accept:
                nfa_p.node(str(item), shape='doublecircle')
            else:
                nfa_p.node(str(item), shape='circle')


        for edge in nfa.edges:
            origin, label = edge
            label = ReplaceUtil() \
                .add_replace('ε', "'ε'") \
                .add_replace(EPSILON, 'ε') \
                .add_replace(' ', "' '") \
                .replace(label)
            for dest in nfa.edges[edge]:
                nfa_p.edge(str(origin), str(dest), label=label)

        nfa_p.attr(rankdir='LR')
        nfa_p.render(view=True, cleanup=True)


    # def test_n2d_convertor(self):
    #     regex_compiler = RegexCompiler()
    #     nfa = regex_compiler.compile("(ab|cd)*abc[ab]")
    #     cvt = N2FConvertor(nfa[1], nfa[0])
    #     dfa = cvt.convert()[1]
    #     print(dfa.edges)

    def test_draw_dfa_picture(self):
        regex_compiler = RegexCompiler()
        nfa = regex_compiler.compile(reg)
        cvt = N2FConvertor(nfa[1], nfa[0])
        cvt_dfa = cvt.convert()


        dfa = cvt_dfa[1]
        dfa_p = Digraph(filename='dfa', format='png')

        for item in dfa.nodes:
            node = dfa.nodes[item]
            if item == cvt_dfa[0]:
                dfa_p.node(str(item), shape='circle', fillcolor="red", style='filled')
            elif node.accept:
                dfa_p.node(str(item), shape='doublecircle')
            else:
                dfa_p.node(str(item), shape='circle')

        for edge in dfa.edges:
            origin, label = edge
            label = ReplaceUtil() \
                .add_replace('ε', "'ε'") \
                .add_replace(EPSILON, 'ε') \
                .add_replace(' ', "' '") \
                .replace(label)

            dfa_p.edge(str(origin), str(dfa.edges[edge]), label=label)

        dfa_p.attr(rankdir='LR')
        dfa_p.render(view=True, cleanup=True)
