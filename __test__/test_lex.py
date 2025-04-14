# @encoding: utf-8
# @author: anishan
# @date: 2025/04/10
# @description: 测试用，屁用没有
import unittest

from graphviz import Digraph

from common.replace_util import ReplaceUtil
from common.type import EPSILON
from lex.regex_compiler import RegexCompiler, N2FConvertor

pattern = "([我-是]|苏联|[内务部])部长*贝利亚，废物贝利亚"


label_convertor = ReplaceUtil() \
    .add_replace(" ", "' '") \
    .add_replace("\n", "\\n") \
    .add_replace("\t", "\\t") \
    .add_replace("\r", "\\r") \
    .add_replace("ε", "'ε'") \
    .add_replace(EPSILON, "ε")


def range_map(fa):
    id_class_map = {}

    def handler(node, *_):
        if node.beg + 1 == node.end:
            label = label_convertor.replace(chr(node.beg))

        else:
            beg = label_convertor.replace(chr(node.beg))
            end = label_convertor.replace(chr(node.end - 1))
            label = f"[{beg}-{end}]"

        id_class_map[node.meta] = label


    fa.range_map.dfs(dlr_handler=handler)

    return id_class_map


def draw(com_fa, filename):

    fa = com_fa[1]
    fa_graph = Digraph(
        filename=filename, format='png',
        graph_attr={'fontname': 'SimHei'},
        node_attr={'fontname': 'SimHei'},
        edge_attr={'fontname': 'SimHei'}
    )



    id_range_map = range_map(fa)

    for item in fa.nodes:
        node = fa.nodes[item]
        if item == com_fa[0]:
            fa_graph.node(str(item), shape='circle', fillcolor="red", style='filled')
        elif node.accept:
            fa_graph.node(str(item), shape='doublecircle')
        else:
            fa_graph.node(str(item), shape='circle')



    for edge in fa.edges:
        origin, label = edge

        label = id_range_map[label]

        if isinstance(fa.edges[edge], set):
            for dest in fa.edges[edge]:
                fa_graph.edge(str(origin), str(dest), label=str(label))
        else:
            fa_graph.edge(str(origin), str(fa.edges[edge]), str(label))


    fa_graph.attr(rankdir='LR')
    fa_graph.render(view=True, cleanup=True)



class TestLex(unittest.TestCase):
    def test_DFA(self):
        compiler = RegexCompiler()
        beg, nfa, end = compiler.compile(pattern)
        # draw((beg, nfa), "nfa")

        cvt = N2FConvertor(nfa, beg)

        cvt_dfa = cvt.convert()

        draw(cvt_dfa, "dfa")

        dfa = cvt_dfa[1]

        state = cvt_dfa[0]
        # for c in pattern:
        #     c = ord(c)
        #     c = dfa.range_map.search(c).meta
        #     state = dfa.translate_to(state, c)
        #
        #     print(dfa.nodes[state])
