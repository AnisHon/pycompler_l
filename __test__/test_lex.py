# @encoding: utf-8
# @author: anishan
# @date: 2025/04/10
# @description: 测试用，屁用没有
import unittest

from graphviz import Digraph

from common.replace_util import ReplaceUtil
from common.common_type import EPSILON
from lex.regex_compiler import RegexCompiler, N2FConvertor, RegexLexer, TokenType, DFAOptimizer

# pattern = "([我-是]|苏联|[内务部])部长*贝利亚，废物贝利亚?"
pattern = "[a-zA-Z0-9_-]+@[a-zA-Z0-9_-]+[\.a-zA-Z0-9_-]+"
# pattern = "\.[0-9]+"

label_convertor = ReplaceUtil() \
    .add_replace(" ", "' '") \
    .add_replace("\n", "\\n") \
    .add_replace("\t", "\\t") \
    .add_replace("\r", "\\r") \
    .add_replace("ε", "'ε'") \
    .add_replace(".", "'.'") \
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
    fa_graph.attr(rankdir='LR', nodesep='0.5', ranksep='1.0')
    fa_graph.attr('node', shape='circle', width='0.5')
    # fa_graph.attr(overlap='scale')  # 自动调整避免重叠
    # fa_graph.attr(splines='true')  # 使用平滑曲线


    id_range_map = range_map(fa)

    for item in fa.nodes:
        node = fa.nodes[item]
        if item == com_fa[0]:
            fa_graph.node(str(item), shape='circle', fillcolor="red", style='filled')
        elif node.accept:
            fa_graph.node(str(item), shape='doublecircle')
        else:
            fa_graph.node(str(item), shape='circle')


    flag = False
    for edge in fa.edges:
        origin, label = edge

        label:str = id_range_map[label]
        if label == "[\x00-􏿿]":
            label = '～'

        label = label.replace('\x00', '\\0')



        if isinstance(fa.edges[edge], set):
            for dest in fa.edges[edge]:
                fa_graph.edge(str(origin), str(dest), label=str(label))
        else:
            if str(origin) == str(fa.edges[edge]):
                fa_graph.edge(str(origin), str(fa.edges[edge]), loopdir= "top" if flag else 'bottom', label=str(label))
                flag = not flag

            else:
                fa_graph.edge(str(origin), str(fa.edges[edge]), label=str(label))


    fa_graph.render(view=True, cleanup=True)

def print_recursive(tokens):
    for item in tokens:
        if item[0] == TokenType.CHAR_CLASS:
            print('[', end='')
            print_recursive(item[1])
            print(']', end='')
        else:
            print(item[1], end='')

class TestRegexLex(unittest.TestCase):
    def test_parse(self):
        tokens = RegexLexer.parse(r"[^a-z]abcd")[0]
        print(tokens)
        # arr = [0, 1, 2, 3]
        # del arr[1:]
        # print()


class TestLex(unittest.TestCase):
    def test_dfa(self):
        compiler = RegexCompiler()
        tokens, rm = RegexLexer.parse(pattern)
        beg, nfa, end = compiler.compile(tokens, rm)
        # draw((beg, nfa), "nfa")

        cvt = N2FConvertor(nfa, beg)

        cvt_dfa = cvt.convert()


        opt = DFAOptimizer(dfa=cvt_dfa[1], origin=cvt_dfa[0])

        origin, dfa = opt.optimize()


        draw((origin, dfa), "dfa")


        state = origin
        for c in "hanjunjie@tgu.edu.cn":
            c = ord(c)
            c = dfa.range_map.search(c).meta
            state = dfa.translate_to(state, c)

            print(dfa.nodes[state])
