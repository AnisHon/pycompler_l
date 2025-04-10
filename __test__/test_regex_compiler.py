import unittest


from common.replace_util import ReplaceUtil
from common.type import EPSILON
from lex.regex_compiler import RegexCompiler
from graphviz import Digraph


class TestRegexCompiler(unittest.TestCase):
    def test_compile(self):
        # print("".join(map(lambda x: x[1], RegexCompiler.lex_regex("a|b(a|b|c)*d[a-c]"))))
        # print(TokenType.priority(TokenType.AND, TokenType.AND))
        regex_compiler = RegexCompiler()
        nfa = regex_compiler.compile("(ab|cd)*abc[a-b] [123kasdfasdf]")
        # print(nfa[1].nodes)
        nfa[1].print_edge()
    def test_draw_nfa_picture(self):

        regex_compiler = RegexCompiler()
        nfa = regex_compiler.compile("(ab|cd)*[abc][a-d]*|s)")[1]

        nfa_p = Digraph(format='png')

        for item in nfa.nodes:
            node = nfa.nodes[item]

            if node.accept:
                nfa_p.node(str(item), shape='doublecircle')
            else:
                nfa_p.node(str(item))

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
        nfa_p.render('dfa', view=True, cleanup=True)

