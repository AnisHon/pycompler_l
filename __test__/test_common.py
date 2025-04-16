import unittest
import random

from graphviz import Digraph

from common.range_map import RangeMap, TreeRangeNode

tree_graph = Digraph(filename='tree', format='png', graph_attr={'fontname': 'Microsoft YaHei'},
        node_attr={'fontname': 'Microsoft YaHei'},
        edge_attr={'fontname': 'Microsoft YaHei'})
def draw_tree(rm: RangeMap, name_handler = lambda node: f"({node.beg},{node.end})", label_handler = lambda node: f"({node.beg},{node.end})\n{node.height}"):

    def handler_add_node(node: TreeRangeNode, *_):

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
        # reg_compiler = RegexCompiler()
        # tokens, range_map = RegexCompiler.lex_regex("你好我是苏联")

        pass
        # print(rm.search(ord('p')).meta)
        # draw_tree(range_map, label_handler=lambda node: f"[{chr(node.beg)}-{chr(node.end - 1)}]\n{node.meta}")

    def test_hack(self):
        hack = [(random.randint(0, 100), random.randint(100, 1000)) for i in range(10)]
        print(hack)
        rm = RangeMap()
        for beg, end in hack:
            rm.insert(beg, end)

        draw_tree(rm)

    def test_(self):
        rm = RangeMap()
        seq = [(0, 1114112), (97, 123), (97, 98), (98, 99), (99, 100), (100, 101)]
        for beg, end in seq[:-2]:
            rm.insert(beg, end)
        rm.insert(99, 100)

        draw_tree(rm)
