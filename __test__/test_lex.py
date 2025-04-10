# @encoding: utf-8
# @author: anishan
# @date: 2025/04/10
# @description: 测试用，屁用没有
import unittest

from graphviz import Digraph
from common.replace_util import ReplaceUtil
from common.type import EPSILON
from lex.regex_compiler import RegexCompiler, N2FConvertor

reg = "say hello to my little friend"


def draw_nfa(com_nfa, filename="nfa_"):
    nfa = com_nfa[1]
    nfa_p = Digraph(filename=filename, format='png')

    nfa_p.render()
    for item in nfa.nodes:
        node = nfa.nodes[item]
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

def draw_dfa(cvt_dfa, filename="dfa_"):
    dfa = cvt_dfa[1]
    dfa_p = Digraph(filename=filename, format='png')

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

class TestRegexCompiler(unittest.TestCase):
    def test_compile(self):
        # print("".join(map(lambda x: x[1], RegexCompiler.lex_regex("a|b(a|b|c)*d[a-c]"))))
        # print(TokenType.priority(TokenType.AND, TokenType.AND))
        regex_compiler = RegexCompiler()

        beg, nfa1, end = regex_compiler.compile("nb")
        beg2, nfa2, end2 = regex_compiler.compile("666")

        nfa1.nodes[end].meta = "nb"
        nfa2.nodes[end2].meta = "666"

        nfa1.concat(nfa2)
        nfa1.add_edge(beg, beg2)

        # print(nfa[1].nodes)
        # nfa[1].print_edge()
        draw_nfa((beg, nfa1, end))
        cvt = N2FConvertor(nfa1, beg)
        cvt_dfa = cvt.convert()
        draw_dfa(cvt_dfa)

        dfa = cvt_dfa[1]
        text = "nmslcnmcnm"
        state = cvt_dfa[0]
        for item in text:
            state = dfa.translate_to(state, item)
            if state is None:
                state = cvt_dfa[0]


            elif dfa.nodes[state].accept:
                print(dfa.nodes[state].meta)
                state = cvt_dfa[0]








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


    def test_n2d_convertor(self):
        regex_compiler = RegexCompiler()
        nfa = regex_compiler.compile("\\{\u1112\(\)\[\]")


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
