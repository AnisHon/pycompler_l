# @encoding: utf-8
# @author: anishan
# @date: 2025/04/10
# @description: 测试用，屁用没有
import pickle
import time
import unittest
from tkinter.constants import DISABLED

from graphviz import Digraph

from common.common_type import EPSILON
from common.range_map import RangeMap
from lex.lexer import Lexer
from common.replace_util import ReplaceUtil
from lex.lexer_builder import CLexerBuilder, CLayeringLexerBuilder
from lex.nfa import NFA
from lex.regex_compiler import RegexCompiler, RegexLexer, TokenType, N2DConvertor, DFAOptimizer
from parser.util import compute_alter_first_set

pattern = "([我-是]|苏联|[内务部])部长*贝利亚，废物贝利亚?"
# pattern = "[a-zA-Z0-9_-]+@[a-zA-Z0-9_-]+[\.a-zA-Z0-9_-]+"
# pattern = "\.[0-9]+"

label_convertor = ReplaceUtil() \
    .add_replace(" ", "' '") \
    .add_replace("\n", "\\n") \
    .add_replace("\t", "\\t") \
    .add_replace("\r", "\\r") \
    .add_replace("ε", "'ε'") \
    .add_replace(".", "'.'") \
    .add_replace(EPSILON, "ε")


def range_table(fa):
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


    id_range_table = range_table(fa)

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

        if label != EPSILON:
            label: str = id_range_table[label]

            label = label.replace('\x00', '\\0')

            if label == "[\x00-􏿿]":
                label = '～'


        # print(origin, label)


        if isinstance(fa, NFA):
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
        tokens = RegexLexer.parse_group([('abc', "a|b|c"), ('efg', 'efg'), ('hijk', '[h-k][hijk]*')])
        print(tokens)
        # arr = [0, 1, 2, 3]
        # del arr[1:]
        # print()

class TestLex(unittest.TestCase):
    def test_dfa(self):
        compiler = RegexCompiler()

        groups, rm = RegexLexer.parse_group([("int", "int"), ("number", "(0[xX])?[0-9]H?")])
        # groups, rm = RegexLexer.parse(r"if|else|int|long|double|([^0-9][a-zA-Z]+[0-9a-zA-Z]+)")
        beg, nfa = compiler.compile_group(groups, rm)

        cvt = N2DConvertor(nfa, beg, enable_multi_label=True)

        origin, dfa = cvt.convert()
        # print(dfa.nodes)
        # draw((origin, dfa), "dfa_")

        opt = DFAOptimizer(dfa=dfa, origin=origin)

        origin, dfa = opt.optimize()


        draw((origin, dfa), "dfa")
        # print()
        state = origin
        # for c in "int":
        #     c = rm.search(c).meta
        #     state = dfa.translate_to(state, c)
        #     print(dfa.nodes[state])


        # state = origin
        # for c in "hanjunjie@tgu.edu.cn":
        #     c = ord(c)
        #     c = dfa.range_map.search(c).meta
        #     state = dfa.translate_to(state, c)

            # print(dfa.nodes[state])

    def test_lexer(self):
        lexer = Lexer([("keyword", r"if|else|int|long|double"), ("identifier", r"[^0-9][_A-Za-z0-9]+")], minimization=False)
        lexer.check()
        origin, dfa = lexer.origin, lexer.dfa

        print(len(dfa.nodes), dfa.edges.__len__())
        # draw((origin, dfa), "dfa")

        state = origin
        for c in "double":
            c = dfa.range_map.search(c).meta
            state = dfa.translate_to(state, c)
            print(state, dfa.nodes[state])




    def test_builder(self):

        c = CLexerBuilder()

        with open("../resource/lex_dump", "rb+") as f:
           c: CLexerBuilder = pickle.load(f)

        dfa = c.lexer.dfa
        print(dfa.nodes.__len__())
        print(dfa.edges.__len__())
        rm: RangeMap = c.lexer.dfa.range_map

        state = c.lexer.origin
        text_ = \
        """
        int main() {
            int a, b, c;
            a = b = c = 10;
            a *= b + c * a;
            printf("Hello World!");
            return 0;
        }
        """
        i = 0
        last_pos = None
        last_state = None
        a = []
        # text_ = "\"hello\";"
        while i < len(text_):

            item: str = text_[i]
            print(item)
            item = rm.search(item).meta
            state = dfa.translate_to(state, item)

            if state is None:
                state = last_state
                i = last_pos
                node = dfa.nodes[state]
                a.append(node.label)
                state = c.lexer.origin

                last_pos = None
                last_state = None

            node = dfa.nodes[state]

            if node.accept:
                last_pos = i
                last_state = state

            i += 1

        a.append(dfa.nodes[state].label)

        print(a)



    def test_layering_builder(self):
        before = time.time()
        builder = CLayeringLexerBuilder()
        edges = 0
        nodes = 0

        for k, v in builder.inner_dfa.items():
            edges += v.dfa.edges.__len__()
            nodes += v.dfa.nodes.__len__()
            print(k, v.dfa.nodes.__len__(), v.dfa.edges.__len__())

            b = []
            def a(x, *_):
                b.append(1)
            v.dfa.range_map.dfs(dlr_handler = a )
            print(b.__len__())
            cnt = 0

        lex = builder.inner_dfa["DFA_COMMENT"]
        state = lex.origin

        for i in "":
            i = lex.dfa.range_map.search(i).meta
            state = lex.dfa.translate_to(state, i)
            print(lex.dfa.nodes[state])

        after = time.time()
        print((after - before) * 1000)
        print(nodes, edges)

