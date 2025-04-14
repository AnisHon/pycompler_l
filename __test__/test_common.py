import random
import unittest

from graphviz import Digraph

from common.range_map import RangeMap, TreeRangeNode
from lex.regex_compiler import RegexCompiler

tree_graph = Digraph(filename='tree', format='png')
def draw_tree(rm: RangeMap, name_handler = lambda node: f"({node.beg},{node.end})", label_handler = lambda node: f"({node.beg},{node.end})\n{node.height}"):

    def handler_add_node(node: TreeRangeNode, l, r):

        name = name_handler(node)
        tree_graph.node(name=name, label=label_handler(node), shape="box")

    def handler_connect_node(node: TreeRangeNode, left: TreeRangeNode, right: TreeRangeNode):

        label = name_handler(node)

        if left is not None:
            label_l = name_handler(left)
            tree_graph.edge(label, label_l, 'L')
        if right is not None:
            label_r = name_handler(right)
            tree_graph.edge(label, label_r, 'R')

    rm.dfs(handler_add_node)
    rm.dfs(handler_connect_node)

    tree_graph.render(view=True, cleanup=True)
    # tree_graph.view()



class TestRangeMap(unittest.TestCase):
    def test_range_map(self):
        rm = RangeMap()
        rm.insert(0, 1)
        rm.insert(1, 2)

        rm.insert(2, 3)
        draw_tree(rm)
        rm.insert(3, 4)
        rm.insert(4, 5)
        rm.insert(5, 6)

    def test_range_map_2(self):
        reg_compiler = RegexCompiler()
        rm = reg_compiler.compile("a|b|c[a-z][abc]i")[1].range_map

        # print(rm.search(ord('p')).meta)
        draw_tree(rm, label_handler=lambda node: f"[{chr(node.beg)}-{chr(node.end - 1)}]\n{node.meta}")

    def test_hack(self):
        hack = [(3, 19), (9, 15), (15, 20), (1, 13), (15, 21), (3, 13), (7, 11), (8, 12), (20, 21), (14, 21)]
        rm = RangeMap()
        for a, b in hack[0:]:
            rm.insert(a, b)

        draw_tree(rm)


